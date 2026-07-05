"""Read-only aggregation queries backing the teacher dashboard.

All queries are scoped to a single teacher's own students - this module never
mutates data and only imports the ORM models owned by other feature modules.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.fee import FeeStructure, Payment, PaymentStatus
from app.models.student import Student
from app.schemas.dashboard import DashboardStatsResponse, RecentActivityEntry

RECENT_ACTIVITY_LIMIT = 10


def _get_attendance_percentage(db: Session, teacher_id: int) -> tuple[float, date]:
    """Return (attendance percentage, reference date) for the most recent date
    on which attendance was recorded for this teacher's students.

    Falls back to (0.0, today) if no attendance has ever been recorded.
    """
    latest_date = (
        db.query(func.max(AttendanceRecord.date))
        .filter(AttendanceRecord.teacher_id == teacher_id)
        .scalar()
    )
    if latest_date is None:
        return 0.0, datetime.now(timezone.utc).date()

    total = (
        db.query(func.count(AttendanceRecord.id))
        .filter(AttendanceRecord.teacher_id == teacher_id, AttendanceRecord.date == latest_date)
        .scalar()
        or 0
    )
    if total == 0:
        return 0.0, latest_date

    attended = (
        db.query(func.count(AttendanceRecord.id))
        .filter(
            AttendanceRecord.teacher_id == teacher_id,
            AttendanceRecord.date == latest_date,
            AttendanceRecord.status.in_([AttendanceStatus.present, AttendanceStatus.late]),
        )
        .scalar()
        or 0
    )
    percentage = round((attended / total) * 100, 2)
    return percentage, latest_date


def _get_overdue_fees_count(db: Session, teacher_id: int) -> int:
    """Count fee structures (for this teacher's students) that are past due
    and not yet fully paid via completed payments.
    """
    today = datetime.now(timezone.utc).date()

    fee_structures = (
        db.query(FeeStructure.id, FeeStructure.amount)
        .join(Student, Student.id == FeeStructure.student_id)
        .filter(Student.teacher_id == teacher_id, FeeStructure.due_date < today)
        .all()
    )
    if not fee_structures:
        return 0

    fee_ids = [row.id for row in fee_structures]
    paid_totals = dict(
        db.query(Payment.fee_structure_id, func.coalesce(func.sum(Payment.amount_paid), 0))
        .filter(Payment.fee_structure_id.in_(fee_ids), Payment.status == PaymentStatus.completed)
        .group_by(Payment.fee_structure_id)
        .all()
    )

    overdue_count = 0
    for row in fee_structures:
        paid = paid_totals.get(row.id, Decimal("0"))
        if paid < row.amount:
            overdue_count += 1
    return overdue_count


def _get_fees_collected_this_month(db: Session, teacher_id: int) -> float:
    """Sum of completed payments made this calendar month for this teacher's students."""
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    total = (
        db.query(func.coalesce(func.sum(Payment.amount_paid), 0))
        .join(Student, Student.id == Payment.student_id)
        .filter(
            Student.teacher_id == teacher_id,
            Payment.status == PaymentStatus.completed,
            Payment.payment_date >= month_start,
        )
        .scalar()
    )
    return float(total or 0)


def _get_recent_activity(db: Session, teacher_id: int) -> list[RecentActivityEntry]:
    """Merge the most recent attendance-marking and payment events into one feed."""
    recent_attendance = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.teacher_id == teacher_id)
        .order_by(AttendanceRecord.created_at.desc())
        .limit(RECENT_ACTIVITY_LIMIT)
        .all()
    )
    recent_payments = (
        db.query(Payment)
        .join(Student, Student.id == Payment.student_id)
        .filter(Student.teacher_id == teacher_id, Payment.status == PaymentStatus.completed)
        .order_by(Payment.created_at.desc())
        .limit(RECENT_ACTIVITY_LIMIT)
        .all()
    )

    entries: list[RecentActivityEntry] = []
    for record in recent_attendance:
        entries.append(
            RecentActivityEntry(
                type="attendance",
                description=f"Attendance marked '{record.status.value}' for student #{record.student_id}",
                timestamp=record.created_at,
            )
        )
    for payment in recent_payments:
        entries.append(
            RecentActivityEntry(
                type="payment",
                description=f"Payment of {payment.amount_paid} received for student #{payment.student_id}",
                timestamp=payment.created_at,
            )
        )

    entries.sort(key=lambda entry: entry.timestamp, reverse=True)
    return entries[:RECENT_ACTIVITY_LIMIT]


def get_teacher_dashboard_stats(db: Session, teacher_id: int) -> DashboardStatsResponse:
    """Aggregate the full set of stats shown on a teacher's dashboard."""
    total_students = (
        db.query(func.count(Student.id))
        .filter(Student.teacher_id == teacher_id, Student.is_active.is_(True))
        .scalar()
        or 0
    )
    attendance_percentage, reference_date = _get_attendance_percentage(db, teacher_id)
    overdue_fees_count = _get_overdue_fees_count(db, teacher_id)
    fees_collected_this_month = _get_fees_collected_this_month(db, teacher_id)
    recent_activity = _get_recent_activity(db, teacher_id)

    return DashboardStatsResponse(
        total_students=total_students,
        attendance_percentage_recent=attendance_percentage,
        attendance_reference_date=reference_date,
        overdue_fees_count=overdue_fees_count,
        total_fees_collected_this_month=fees_collected_this_month,
        recent_activity=recent_activity,
    )
