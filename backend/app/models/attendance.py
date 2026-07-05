"""Attendance record model."""
import enum
from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.user import User


class AttendanceStatus(str, enum.Enum):
    """Possible attendance outcomes for a student on a given day."""

    present = "present"
    absent = "absent"
    late = "late"


class AttendanceRecord(Base, TimestampMixin):
    """A single student's attendance status for a single date."""

    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, name="attendance_status"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="attendance_records")
    teacher: Mapped["User"] = relationship("User")
