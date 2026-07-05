"""Business logic for marking, querying, and summarizing student attendance."""
import calendar
from datetime import date as date_type

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.exceptions import ForbiddenError, NotFoundError
from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.attendance import AttendanceEntry, AttendanceSummaryResponse, CalendarSummaryResponse


def _get_student_for_teacher(db: Session, student_id: int, teacher: User) -> Student:
    """Fetch a student, ensuring it belongs to `teacher`.

    Raises NotFoundError if the student does not exist, ForbiddenError if it
    belongs to a different teacher.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student")
    if student.teacher_id != teacher.id:
        raise ForbiddenError("You do not have access to this student")
    return student


def _get_student_for_viewer(db: Session, student_id: int, user: User) -> Student:
    """Fetch a student, ensuring `user` (teacher or parent) may view it."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student")

    if user.role == UserRole.teacher:
        if student.teacher_id != user.id:
            raise ForbiddenError("You do not have access to this student")
    elif user.role == UserRole.parent:
        if student.parent_user_id != user.id:
            raise ForbiddenError("You do not have access to this student")
    # admins fall through with unrestricted read access

    return student


def _upsert_entry(db: Session, entry: AttendanceEntry, teacher: User) -> AttendanceRecord:
    """Insert or update the single AttendanceRecord keyed on (student_id, date).

    Verifies the student belongs to `teacher` before writing.
    """
    _get_student_for_teacher(db, entry.student_id, teacher)

    record = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.student_id == entry.student_id,
            AttendanceRecord.date == entry.date,
        )
        .first()
    )

    if record:
        record.status = entry.status
        record.notes = entry.notes
        record.teacher_id = teacher.id
    else:
        record = AttendanceRecord(
            student_id=entry.student_id,
            teacher_id=teacher.id,
            date=entry.date,
            status=entry.status,
            notes=entry.notes,
        )
        db.add(record)

    return record


def mark_attendance(db: Session, entry: AttendanceEntry, teacher: User) -> AttendanceRecord:
    """Mark (create or update) attendance for a single student on a single date."""
    record = _upsert_entry(db, entry, teacher)
    db.commit()
    db.refresh(record)
    return record


def bulk_mark_attendance(
    db: Session, entries: list[AttendanceEntry], teacher: User
) -> list[AttendanceRecord]:
    """Mark (create or update) attendance for many students/dates in one transaction."""
    records = [_upsert_entry(db, entry, teacher) for entry in entries]
    db.commit()
    for record in records:
        db.refresh(record)
    return records


def update_attendance(
    db: Session,
    record_id: int,
    teacher: User,
    status: AttendanceStatus | None,
    notes: str | None,
) -> AttendanceRecord:
    """Update an existing attendance record's status/notes.

    Only the teacher who owns the underlying student may update it.
    """
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise NotFoundError("Attendance record")
    if record.teacher_id != teacher.id:
        raise ForbiddenError("You do not have access to this attendance record")

    if status is not None:
        record.status = status
    if notes is not None:
        record.notes = notes

    db.commit()
    db.refresh(record)
    return record


def query_attendance(
    db: Session,
    current_user: User,
    date: date_type | None = None,
    class_grade: str | None = None,
    student_id: int | None = None,
) -> list[AttendanceRecord]:
    """Role-scoped attendance query.

    Teachers see records for their own students; parents see records for
    their own linked children; admins see everything. Optional filters
    further narrow the result.
    """
    query = db.query(AttendanceRecord).join(Student, AttendanceRecord.student_id == Student.id)

    if current_user.role == UserRole.teacher:
        query = query.filter(Student.teacher_id == current_user.id)
    elif current_user.role == UserRole.parent:
        query = query.filter(Student.parent_user_id == current_user.id)
    # admin: unrestricted

    if date is not None:
        query = query.filter(AttendanceRecord.date == date)
    if class_grade is not None:
        query = query.filter(Student.class_grade == class_grade)
    if student_id is not None:
        query = query.filter(AttendanceRecord.student_id == student_id)

    return query.order_by(AttendanceRecord.date.desc()).all()


def get_attendance_summary(
    db: Session, current_user: User, student_id: int
) -> AttendanceSummaryResponse:
    """Compute a student's attendance percentage and present/absent/late breakdown."""
    _get_student_for_viewer(db, student_id, current_user)

    rows = (
        db.query(AttendanceRecord.status, func.count(AttendanceRecord.id))
        .filter(AttendanceRecord.student_id == student_id)
        .group_by(AttendanceRecord.status)
        .all()
    )

    counts = {AttendanceStatus.present: 0, AttendanceStatus.absent: 0, AttendanceStatus.late: 0}
    for status, count in rows:
        counts[AttendanceStatus(status)] = count

    total_days = sum(counts.values())
    present_days = counts[AttendanceStatus.present]
    absent_days = counts[AttendanceStatus.absent]
    late_days = counts[AttendanceStatus.late]
    percentage = round((present_days / total_days) * 100, 2) if total_days else 0.0

    return AttendanceSummaryResponse(
        student_id=student_id,
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        late_days=late_days,
        attendance_percentage=percentage,
    )


def get_calendar_summary(
    db: Session, teacher: User, year: int, month: int
) -> CalendarSummaryResponse:
    """Per-date present/absent/late/total breakdown for every day in the given
    month that has at least one attendance record, scoped to `teacher`'s own
    students. Uses a single grouped query to avoid per-day round trips.
    """
    _, days_in_month = calendar.monthrange(year, month)
    start = date_type(year, month, 1)
    end = date_type(year, month, days_in_month)

    rows = (
        db.query(AttendanceRecord.date, AttendanceRecord.status, func.count(AttendanceRecord.id))
        .join(Student, AttendanceRecord.student_id == Student.id)
        .filter(Student.teacher_id == teacher.id)
        .filter(AttendanceRecord.date >= start, AttendanceRecord.date <= end)
        .group_by(AttendanceRecord.date, AttendanceRecord.status)
        .all()
    )

    per_day: dict[date_type, dict[str, int]] = {}
    for record_date, status, count in rows:
        counts = per_day.setdefault(
            record_date,
            {
                AttendanceStatus.present.value: 0,
                AttendanceStatus.absent.value: 0,
                AttendanceStatus.late.value: 0,
            },
        )
        counts[AttendanceStatus(status).value] = count

    days = [
        {
            "date": record_date,
            "present": counts[AttendanceStatus.present.value],
            "absent": counts[AttendanceStatus.absent.value],
            "late": counts[AttendanceStatus.late.value],
            "total": sum(counts.values()),
        }
        for record_date, counts in sorted(per_day.items())
    ]

    return CalendarSummaryResponse(days=days)
