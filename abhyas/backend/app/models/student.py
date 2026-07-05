"""Student model."""
from datetime import date as date_type
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.attendance import AttendanceRecord
    from app.models.fee import FeeStructure
    from app.models.user import User


class Student(Base, TimestampMixin):
    """A student managed by a teacher, optionally linked to a parent account."""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    date_of_birth: Mapped[date_type] = mapped_column(Date, nullable=False)
    class_grade: Mapped[str] = mapped_column(String(20), nullable=False)
    section: Mapped[str | None] = mapped_column(String(20), nullable=True)
    roll_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parent_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    parent_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    parent_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    parent_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    enrollment_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    scheduled_days: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    monthly_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    teacher: Mapped["User"] = relationship("User", foreign_keys=[teacher_id], back_populates="students")
    parent_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[parent_user_id], back_populates="children"
    )
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        "AttendanceRecord", back_populates="student", cascade="all, delete-orphan"
    )
    fee_structures: Mapped[list["FeeStructure"]] = relationship(
        "FeeStructure", back_populates="student", cascade="all, delete-orphan"
    )
