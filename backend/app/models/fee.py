"""Fee structure, payment, and fee reminder models."""
import enum
from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.student import Student


class FeeFrequency(str, enum.Enum):
    """How often a fee structure recurs."""

    monthly = "monthly"
    term = "term"
    one_time = "one_time"


class PaymentMethod(str, enum.Enum):
    """Channel through which a payment was made."""

    razorpay = "razorpay"
    cash = "cash"
    bank_transfer = "bank_transfer"


class PaymentStatus(str, enum.Enum):
    """Lifecycle status of a payment."""

    pending = "pending"
    completed = "completed"
    failed = "failed"


class ReminderChannel(str, enum.Enum):
    """Channel used to deliver a fee reminder."""

    email = "email"


class ReminderStatus(str, enum.Enum):
    """Delivery outcome of a fee reminder."""

    sent = "sent"
    failed = "failed"


class FeeStructure(Base, TimestampMixin):
    """A recurring or one-time fee owed by a student."""

    __tablename__ = "fee_structures"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    frequency: Mapped[FeeFrequency] = mapped_column(SAEnum(FeeFrequency, name="fee_frequency"), nullable=False)
    due_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    billing_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    billing_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="fee_structures")
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="fee_structure", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["FeeReminder"]] = relationship(
        "FeeReminder", back_populates="fee_structure", cascade="all, delete-orphan"
    )


class Payment(Base):
    """A payment made (or attempted) against a fee structure."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fee_structure_id: Mapped[int] = mapped_column(
        ForeignKey("fee_structures.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(SAEnum(PaymentMethod, name="payment_method"), nullable=False)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status"), nullable=False, default=PaymentStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    fee_structure: Mapped["FeeStructure"] = relationship("FeeStructure", back_populates="payments")
    student: Mapped["Student"] = relationship("Student")


class FeeReminder(Base):
    """A record of a fee reminder sent (or attempted) to a parent."""

    __tablename__ = "fee_reminders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_structure_id: Mapped[int] = mapped_column(
        ForeignKey("fee_structures.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    channel: Mapped[ReminderChannel] = mapped_column(
        SAEnum(ReminderChannel, name="reminder_channel"), nullable=False, default=ReminderChannel.email
    )
    status: Mapped[ReminderStatus] = mapped_column(SAEnum(ReminderStatus, name="reminder_status"), nullable=False)

    student: Mapped["Student"] = relationship("Student")
    fee_structure: Mapped["FeeStructure"] = relationship("FeeStructure", back_populates="reminders")
