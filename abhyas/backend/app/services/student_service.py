"""Business logic for the Students module.

Role-based access rules (see CLAUDE.md):
  - Teachers may only access students where teacher_id == current_user.id.
  - Parents may only read students where parent_user_id == current_user.id.
  - Admins access student data via /admin/* routes only (not implemented here).
"""
import calendar
import logging
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.exceptions import ForbiddenError, NotFoundError
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.student import StudentCreate, StudentUpdate

logger = logging.getLogger(__name__)

# Maps the lowercase 3-letter weekday codes used by the UI/API to the value
# returned by Python's `date.weekday()` (Monday=0 .. Sunday=6). Note the UI's
# codes are Sunday-first in intent ("sun" first) but Python's weekday() is
# Monday-first, so this mapping is the single place that reconciles the two.
_WEEKDAY_CODE_TO_PY_WEEKDAY: dict[str, int] = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def calculate_monthly_fee(
    daily_fee: Decimal | None, scheduled_days: list[str], year: int, month: int
) -> Decimal:
    """Compute the monthly fee for a student given a daily fee and the set of
    weekdays (lowercase 3-letter codes) they have class each week.

    Iterates every day in (year, month) and multiplies `daily_fee` by the
    count of days landing on any of the scheduled weekdays. Returns
    Decimal("0.00") if there is no daily fee or no scheduled days.
    """
    if daily_fee is None or not scheduled_days:
        return Decimal("0.00")

    target_weekdays = {_WEEKDAY_CODE_TO_PY_WEEKDAY[code] for code in scheduled_days}
    _, days_in_month = calendar.monthrange(year, month)

    matching_day_count = sum(
        1
        for day in range(1, days_in_month + 1)
        if date(year, month, day).weekday() in target_weekdays
    )

    return (daily_fee * matching_day_count).quantize(Decimal("0.01"))


def create_student(db: Session, teacher: User, payload: StudentCreate) -> Student:
    """Create a new student owned by the given teacher.

    If the payload provides `daily_fee` and/or `scheduled_days` but does not
    explicitly set `monthly_fee`, the monthly fee is auto-computed for the
    current real-world month. An explicitly provided `monthly_fee` is always
    honored as a manual override.
    """
    data = payload.model_dump()
    fields_set = payload.model_fields_set

    if "monthly_fee" not in fields_set and (
        "daily_fee" in fields_set or "scheduled_days" in fields_set
    ):
        today = date.today()
        data["monthly_fee"] = calculate_monthly_fee(
            data.get("daily_fee"), data.get("scheduled_days") or [], today.year, today.month
        )

    student = Student(teacher_id=teacher.id, **data)
    db.add(student)
    db.commit()
    db.refresh(student)
    logger.info("Student %s created by teacher %s", student.id, teacher.id)
    return student


def get_students_for_user(
    db: Session,
    current_user: User,
    class_grade: str | None = None,
    section: str | None = None,
) -> list[Student]:
    """List students visible to the current user, branching on role.

    Teachers see their own roster (optionally filtered by class/section).
    Parents see only the student(s) linked to their account via parent_user_id.
    """
    query = db.query(Student)

    if current_user.role == UserRole.teacher:
        query = query.filter(Student.teacher_id == current_user.id)
    elif current_user.role == UserRole.parent:
        query = query.filter(Student.parent_user_id == current_user.id)
    else:
        # Admins use /admin/* routes for cross-tenant access, not this router.
        raise ForbiddenError("Use /admin/* routes to access student data as an admin")

    if class_grade:
        query = query.filter(Student.class_grade == class_grade)
    if section:
        query = query.filter(Student.section == section)

    return query.order_by(Student.full_name).all()


def _assert_can_access(student: Student, current_user: User) -> None:
    """Raise ForbiddenError unless the current user may view this student."""
    if current_user.role == UserRole.teacher and student.teacher_id == current_user.id:
        return
    if current_user.role == UserRole.parent and student.parent_user_id == current_user.id:
        return
    raise ForbiddenError("You do not have access to this student")


def _assert_can_write(student: Student, current_user: User) -> None:
    """Raise ForbiddenError unless the current user may modify this student.

    Parents are never allowed to write, regardless of linkage.
    """
    if current_user.role == UserRole.teacher and student.teacher_id == current_user.id:
        return
    raise ForbiddenError("You do not have permission to modify this student")


def get_student_by_id(db: Session, student_id: int, current_user: User) -> Student:
    """Fetch a single student, enforcing ownership/linkage checks."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student")
    _assert_can_access(student, current_user)
    return student


def update_student(
    db: Session, student_id: int, current_user: User, payload: StudentUpdate
) -> Student:
    """Update a student's fields. Teacher-only, ownership-checked.

    If the update payload touches `daily_fee` and/or `scheduled_days` without
    also explicitly setting `monthly_fee` in that same request, `monthly_fee`
    is recomputed for the current real-world month. An explicitly provided
    `monthly_fee` in the payload is always honored as a manual override.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student")
    _assert_can_write(student, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    should_recompute = "monthly_fee" not in update_data and (
        "daily_fee" in update_data or "scheduled_days" in update_data
    )

    for field, value in update_data.items():
        setattr(student, field, value)

    if should_recompute:
        today = date.today()
        student.monthly_fee = calculate_monthly_fee(
            student.daily_fee, student.scheduled_days or [], today.year, today.month
        )

    db.commit()
    db.refresh(student)
    logger.info("Student %s updated by teacher %s", student.id, current_user.id)
    return student


def deactivate_student(db: Session, student_id: int, current_user: User) -> Student:
    """Soft-delete a student by setting is_active=False. Teacher-only."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student")
    _assert_can_write(student, current_user)

    student.is_active = False
    db.commit()
    db.refresh(student)
    logger.info("Student %s deactivated by teacher %s", student.id, current_user.id)
    return student


def get_monthly_fee_preview(
    db: Session, student_id: int, current_user: User, year: int, month: int
) -> Decimal:
    """Compute (without persisting) what the monthly fee would be for the
    given year/month, using the student's currently stored daily_fee and
    scheduled_days. Access-checked the same way as get_student_by_id.
    """
    student = get_student_by_id(db, student_id, current_user)
    return calculate_monthly_fee(student.daily_fee, student.scheduled_days or [], year, month)


def invite_parent(
    db: Session,
    student_id: int,
    current_user: User,
    parent_email: str,
    parent_name: str | None,
) -> tuple[Student, bool, int | None, str]:
    """Record a parent invite for a student.

    NOTE: The Auth module's email-sending service is not built yet, so this does
    NOT send a real email. Behavior:
      - Store parent_email/parent_name on the Student row (pending invite state).
      - If a parent User account with this email already exists, link it
        immediately via parent_user_id (no separate "accept invite" step needed
        since the account already exists).
      - Otherwise, parent_user_id stays null until the parent registers with
        this email address; the Auth module's registration flow (or a future
        "accept invite" endpoint) is expected to complete the link then.

    Returns (student, invited, parent_user_id, message) for the router to build
    a ParentInviteResponse.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student")
    _assert_can_write(student, current_user)

    student.parent_email = parent_email
    if parent_name:
        student.parent_name = parent_name

    existing_parent = (
        db.query(User)
        .filter(User.email == parent_email, User.role == UserRole.parent)
        .first()
    )

    if existing_parent:
        student.parent_user_id = existing_parent.id
        message = "Existing parent account found and linked to this student."
        invited = True
    else:
        message = (
            "No parent account exists yet for this email. The invite has been "
            "recorded; the link will complete once the parent registers with "
            "this email (email delivery is not yet implemented)."
        )
        invited = True

    db.commit()
    db.refresh(student)
    logger.info(
        "Parent invite recorded for student %s by teacher %s (email=%s, linked=%s)",
        student.id,
        current_user.id,
        parent_email,
        existing_parent is not None,
    )
    return student, invited, student.parent_user_id, message
