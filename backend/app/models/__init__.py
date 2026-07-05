"""ORM models package.

Every model must be imported here so that Alembic's autogenerate can discover
all tables via `Base.metadata` when this package is imported.
"""
from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.fee import (
    FeeFrequency,
    FeeReminder,
    FeeStructure,
    Payment,
    PaymentMethod,
    PaymentStatus,
    ReminderChannel,
    ReminderStatus,
)
from app.models.student import Student
from app.models.user import RefreshToken, User, UserRole

__all__ = [
    "AttendanceRecord",
    "AttendanceStatus",
    "FeeFrequency",
    "FeeReminder",
    "FeeStructure",
    "Payment",
    "PaymentMethod",
    "PaymentStatus",
    "ReminderChannel",
    "ReminderStatus",
    "RefreshToken",
    "Student",
    "User",
    "UserRole",
]
