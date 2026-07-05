"""Business logic for the admin panel: user management and platform stats."""
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError
from app.models.fee import Payment, PaymentStatus
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.admin import AdminStatsResponse, AdminUserUpdateRequest


def list_all_users(db: Session) -> list[User]:
    """Return every user account on the platform."""
    return db.query(User).order_by(User.created_at.desc()).all()


def update_user(db: Session, user_id: int, payload: AdminUserUpdateRequest) -> User:
    """Update an account's active status and/or role.

    Raises NotFoundError if the user doesn't exist, or ConflictError if the
    change would demote/deactivate the last remaining active admin - the
    platform must always retain at least one active admin account.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User")

    is_demoting_admin = user.role == UserRole.admin and (
        (payload.role is not None and payload.role != UserRole.admin)
        or payload.is_active is False
    )
    if is_demoting_admin:
        active_admin_count = (
            db.query(User)
            .filter(User.role == UserRole.admin, User.is_active.is_(True))
            .count()
        )
        if active_admin_count <= 1:
            raise ConflictError("Cannot remove the last active admin account")

    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        user.role = payload.role

    db.commit()
    db.refresh(user)
    return user


def get_platform_stats(db: Session) -> AdminStatsResponse:
    """Aggregate platform-wide counts for the admin dashboard."""
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_teachers = db.query(func.count(User.id)).filter(User.role == UserRole.teacher).scalar() or 0
    total_parents = db.query(func.count(User.id)).filter(User.role == UserRole.parent).scalar() or 0
    total_students = db.query(func.count(Student.id)).scalar() or 0

    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    total_payments_this_month = (
        db.query(func.coalesce(func.sum(Payment.amount_paid), 0))
        .filter(Payment.status == PaymentStatus.completed, Payment.payment_date >= month_start)
        .scalar()
    )

    return AdminStatsResponse(
        total_users=total_users,
        total_teachers=total_teachers,
        total_parents=total_parents,
        total_students=total_students,
        total_payments_this_month=float(total_payments_this_month or 0),
    )
