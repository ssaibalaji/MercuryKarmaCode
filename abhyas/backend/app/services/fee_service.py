"""Business logic for the Fees & Payments module.

Role-based access rules (see CLAUDE.md):
  - Teachers manage fee structures for their own students only.
  - Parents may view + pay for their own linked children only.
  - Outstanding balance = FeeStructure.amount - sum(completed Payments) for that fee.
  - Fee reminders only for fees past due_date with outstanding balance > 0.
  - Payment.status may only be moved to `completed` by the verified Razorpay
    webhook handler (record_payment_from_webhook) - never by a client-facing call.
"""
import calendar
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import extract
from sqlalchemy.orm import Session, selectinload

from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.attendance import AttendanceRecord
from app.models.fee import FeeFrequency, FeeReminder, FeeStructure, Payment, PaymentMethod, PaymentStatus, ReminderChannel, ReminderStatus
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.fee import (
    FeeDetailResponse,
    FeeGenerationSummaryResponse,
    FeeStructureCreate,
    FeeStructureUpdate,
    FeeStructureWithBalance,
    GeneratedFeeEntry,
    PaymentResponse,
)
from app.services import email_service, razorpay_service

logger = logging.getLogger(__name__)


def _outstanding_balance(fee: FeeStructure) -> Decimal:
    """Outstanding balance for a fee structure: amount minus completed payments."""
    completed_paid = sum(
        (p.amount_paid for p in fee.payments if p.status == PaymentStatus.completed),
        Decimal("0"),
    )
    return fee.amount - completed_paid


def _is_overdue(fee: FeeStructure, balance: Decimal, *, today: date | None = None) -> bool:
    today = today or date.today()
    return balance > 0 and fee.due_date < today


def _to_with_balance(fee: FeeStructure) -> FeeStructureWithBalance:
    balance = _outstanding_balance(fee)
    return FeeStructureWithBalance(
        id=fee.id,
        student_id=fee.student_id,
        student_name=fee.student.full_name,
        amount=fee.amount,
        frequency=fee.frequency,
        due_date=fee.due_date,
        description=fee.description,
        created_at=fee.created_at,
        updated_at=fee.updated_at,
        outstanding_balance=balance,
        is_overdue=_is_overdue(fee, balance),
    )


def _assert_can_access_student(student: Student, current_user: User) -> None:
    """Raise ForbiddenError unless the current user may view this student's fees."""
    if current_user.role == UserRole.teacher and student.teacher_id == current_user.id:
        return
    if current_user.role == UserRole.parent and student.parent_user_id == current_user.id:
        return
    raise ForbiddenError("You do not have access to this student's fees")


def _get_student_or_404(db: Session, student_id: int) -> Student:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student")
    return student


def create_fee_structure(db: Session, teacher: User, payload: FeeStructureCreate) -> FeeStructure:
    """Create a fee structure for a student owned by `teacher`."""
    student = _get_student_or_404(db, payload.student_id)
    if student.teacher_id != teacher.id:
        raise ForbiddenError("You may only manage fees for your own students")

    fee = FeeStructure(
        student_id=payload.student_id,
        amount=payload.amount,
        frequency=payload.frequency,
        due_date=payload.due_date,
        description=payload.description,
    )
    db.add(fee)
    db.commit()
    db.refresh(fee)
    logger.info("Fee structure %s created for student %s by teacher %s", fee.id, student.id, teacher.id)
    return fee


def update_fee_structure(db: Session, teacher: User, fee_id: int, payload: FeeStructureUpdate) -> FeeStructure:
    """Update a fee structure. Teacher-only, ownership-checked."""
    fee = db.query(FeeStructure).filter(FeeStructure.id == fee_id).first()
    if not fee:
        raise NotFoundError("Fee structure")
    if fee.student.teacher_id != teacher.id:
        raise ForbiddenError("You may only manage fees for your own students")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(fee, field, value)

    db.commit()
    db.refresh(fee)
    logger.info("Fee structure %s updated by teacher %s", fee.id, teacher.id)
    return fee


def get_fee_detail(db: Session, current_user: User, student_id: int) -> FeeDetailResponse:
    """Fee structures + payment history + outstanding balance for one student."""
    student = _get_student_or_404(db, student_id)
    _assert_can_access_student(student, current_user)

    fees = (
        db.query(FeeStructure)
        .options(selectinload(FeeStructure.payments), selectinload(FeeStructure.student))
        .filter(FeeStructure.student_id == student_id)
        .order_by(FeeStructure.due_date)
        .all()
    )

    structures: list[FeeStructureWithBalance] = []
    all_payments: list[Payment] = []
    total_outstanding = Decimal("0")
    for fee in fees:
        with_balance = _to_with_balance(fee)
        structures.append(with_balance)
        total_outstanding += with_balance.outstanding_balance
        all_payments.extend(fee.payments)

    all_payments.sort(key=lambda p: p.payment_date, reverse=True)

    return FeeDetailResponse(
        student_id=student_id,
        fee_structures=structures,
        payments=[PaymentResponse.model_validate(p) for p in all_payments],
        total_outstanding=total_outstanding,
    )


def list_overdue_fees(db: Session, teacher: User) -> list[FeeStructureWithBalance]:
    """Fee structures past due_date with outstanding balance > 0, for the teacher's own students."""
    today = date.today()
    fees = (
        db.query(FeeStructure)
        .options(selectinload(FeeStructure.payments), selectinload(FeeStructure.student))
        .join(Student, FeeStructure.student_id == Student.id)
        .filter(Student.teacher_id == teacher.id, FeeStructure.due_date < today)
        .all()
    )
    overdue: list[FeeStructureWithBalance] = []
    for fee in fees:
        with_balance = _to_with_balance(fee)
        if with_balance.outstanding_balance > 0:
            overdue.append(with_balance)
    return overdue


def send_reminder(db: Session, teacher: User, fee_id: int) -> FeeReminder:
    """Manually trigger a fee reminder email. Only allowed for overdue fees with a balance."""
    fee = db.query(FeeStructure).filter(FeeStructure.id == fee_id).first()
    if not fee:
        raise NotFoundError("Fee structure")
    student = fee.student
    if student.teacher_id != teacher.id:
        raise ForbiddenError("You may only manage fees for your own students")

    balance = _outstanding_balance(fee)
    if not _is_overdue(fee, balance):
        raise ConflictError("Fee is not overdue or has no outstanding balance")
    if not student.parent_email:
        raise ConflictError("Student has no parent email on file")

    sent = email_service.send_email(
        to=student.parent_email,
        subject=f"Fee payment reminder for {student.full_name}",
        body=(
            f"Dear parent, a fee of {balance} for {student.full_name} was due on "
            f"{fee.due_date}. Please make payment at your earliest convenience."
        ),
    )

    reminder = FeeReminder(
        student_id=student.id,
        fee_structure_id=fee.id,
        channel=ReminderChannel.email,
        status=ReminderStatus.sent if sent else ReminderStatus.failed,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    logger.info("Fee reminder %s sent for fee structure %s by teacher %s", reminder.id, fee.id, teacher.id)
    return reminder


def mark_fee_paid(db: Session, teacher: User, fee_id: int) -> FeeStructureWithBalance:
    """Manually record a fee as fully paid (cash/offline payment). Teacher-only.

    This is an additive cash-payment recording path, distinct from the
    Razorpay webhook flow which remains the ONLY path allowed to complete
    `razorpay`-method payments (record_payment_from_webhook).
    """
    fee = db.query(FeeStructure).filter(FeeStructure.id == fee_id).first()
    if not fee:
        raise NotFoundError("Fee structure")
    if fee.student.teacher_id != teacher.id:
        raise ForbiddenError("You may only manage fees for your own students")

    balance = _outstanding_balance(fee)
    if balance <= 0:
        raise ConflictError("This fee is already fully paid")

    payment = Payment(
        fee_structure_id=fee.id,
        student_id=fee.student_id,
        amount_paid=balance,
        payment_date=datetime.now(timezone.utc),
        method=PaymentMethod.cash,
        status=PaymentStatus.completed,
    )
    db.add(payment)
    db.commit()
    db.refresh(fee)
    logger.info("Fee structure %s marked paid (cash) by teacher %s", fee.id, teacher.id)
    return _to_with_balance(fee)


def create_payment_order(db: Session, current_user: User, fee_structure_id: int) -> tuple[Payment, dict[str, Any]]:
    """Create a pending Payment row + Razorpay order for a fee's outstanding balance."""
    fee = db.query(FeeStructure).filter(FeeStructure.id == fee_structure_id).first()
    if not fee:
        raise NotFoundError("Fee structure")
    student = fee.student
    _assert_can_access_student(student, current_user)

    balance = _outstanding_balance(fee)
    if balance <= 0:
        raise ConflictError("This fee has no outstanding balance")

    order = razorpay_service.create_order(balance, student.id)

    payment = Payment(
        fee_structure_id=fee.id,
        student_id=student.id,
        amount_paid=balance,
        payment_date=datetime.now(timezone.utc),
        method=PaymentMethod.razorpay,
        razorpay_order_id=order["id"],
        status=PaymentStatus.pending,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    logger.info("Pending payment %s created for fee structure %s (order=%s)", payment.id, fee.id, order["id"])
    return payment, order


def get_payment_history(db: Session, current_user: User, student_id: int) -> list[Payment]:
    """Role-scoped payment history for a student."""
    student = _get_student_or_404(db, student_id)
    _assert_can_access_student(student, current_user)
    return (
        db.query(Payment)
        .filter(Payment.student_id == student_id)
        .order_by(Payment.payment_date.desc())
        .all()
    )


def record_payment_from_webhook(db: Session, payload: dict[str, Any]) -> Payment | None:
    """Update a Payment's status from a *verified* Razorpay webhook payload.

    This is the ONLY path allowed to transition a Payment to `completed`. The
    caller (router) MUST have already verified the webhook signature before
    calling this. Idempotent: re-delivered webhooks for an already-settled
    payment are a no-op.
    """
    event = payload.get("event", "")
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = entity.get("order_id")
    razorpay_payment_id = entity.get("id")

    if not order_id:
        logger.warning("Razorpay webhook payload missing order_id; event=%s", event)
        raise NotFoundError("Payment")

    payment = db.query(Payment).filter(Payment.razorpay_order_id == order_id).first()
    if not payment:
        logger.warning("No pending payment found for Razorpay order %s", order_id)
        raise NotFoundError("Payment")

    if payment.status != PaymentStatus.pending:
        logger.info("Ignoring webhook for already-settled payment %s (status=%s)", payment.id, payment.status)
        return payment

    if event == "payment.captured":
        payment.status = PaymentStatus.completed
        payment.razorpay_payment_id = razorpay_payment_id
        payment.payment_date = datetime.now(timezone.utc)
        logger.info("Payment %s marked completed via webhook (order=%s)", payment.id, order_id)
    elif event == "payment.failed":
        payment.status = PaymentStatus.failed
        payment.razorpay_payment_id = razorpay_payment_id
        logger.info("Payment %s marked failed via webhook (order=%s)", payment.id, order_id)
    else:
        logger.info("Ignoring unhandled Razorpay webhook event: %s", event)
        return payment

    db.commit()
    db.refresh(payment)
    return payment


def generate_fees_from_attendance(db: Session, teacher_id: int) -> FeeGenerationSummaryResponse:
    """Auto-generate monthly FeeStructure rows for past months with attendance activity.

    For every student of `teacher_id`, and every past calendar month (strictly
    before the current month) with at least one logged AttendanceRecord (used
    only as a signal that the student was enrolled/attending that month), bill
    the student's stored `Student.monthly_fee` value - irrespective of actual
    attendance status (present/absent/late has no bearing on the billed
    amount) and irrespective of which month is being billed (the same stored
    monthly fee is applied to every qualifying past month). `monthly_fee` is
    normally auto-computed from `daily_fee`/`scheduled_days` but may also be a
    manual override set by the teacher - either way, whatever is currently
    stored on the student is what gets billed.

    A given (student, year, month) that was already auto-generated is only
    ever regenerated (its amount recalculated to the student's current
    `monthly_fee`) if it has NOT been fully paid yet. Once a fee has a
    completed payment covering it in full, it is permanently locked and
    skipped on every subsequent run.
    """
    today = date.today()
    current_year, current_month = today.year, today.month

    combos = (
        db.query(
            AttendanceRecord.student_id,
            extract("year", AttendanceRecord.date).label("year"),
            extract("month", AttendanceRecord.date).label("month"),
        )
        .join(Student, AttendanceRecord.student_id == Student.id)
        .filter(Student.teacher_id == teacher_id)
        .distinct()
        .all()
    )

    created: list[GeneratedFeeEntry] = []
    updated: list[GeneratedFeeEntry] = []
    skipped_already_generated = 0
    skipped_no_daily_fee = 0
    skipped_zero_days = 0

    for student_id, year_raw, month_raw in combos:
        year, month = int(year_raw), int(month_raw)
        if (year, month) >= (current_year, current_month):
            continue

        student = db.query(Student).filter(Student.id == student_id).first()
        if student is None or student.monthly_fee is None:
            skipped_no_daily_fee += 1
            continue

        amount = student.monthly_fee
        if amount == 0:
            skipped_zero_days += 1
            continue

        existing = (
            db.query(FeeStructure)
            .options(selectinload(FeeStructure.payments))
            .filter(
                FeeStructure.student_id == student_id,
                FeeStructure.billing_year == year,
                FeeStructure.billing_month == month,
                FeeStructure.is_auto_generated.is_(True),
            )
            .first()
        )

        if existing is not None:
            if _outstanding_balance(existing) <= 0:
                skipped_already_generated += 1
                continue

            existing.amount = amount
            updated.append(
                GeneratedFeeEntry(
                    student_id=student_id,
                    student_name=student.full_name,
                    year=year,
                    month=month,
                    amount=amount,
                )
            )
            continue

        if month == 12:
            due_date = date(year + 1, 1, 1)
        else:
            due_date = date(year, month + 1, 1)

        fee = FeeStructure(
            student_id=student_id,
            amount=amount,
            frequency=FeeFrequency.monthly,
            due_date=due_date,
            description=f"Auto-generated fee for {calendar.month_name[month]} {year} (from student's monthly fee)",
            billing_year=year,
            billing_month=month,
            is_auto_generated=True,
        )
        db.add(fee)
        created.append(
            GeneratedFeeEntry(
                student_id=student_id,
                student_name=student.full_name,
                year=year,
                month=month,
                amount=amount,
            )
        )

    db.commit()
    logger.info(
        "Generated %d / updated %d auto fee(s) from attendance for teacher %s "
        "(skipped: already_generated=%d, no_daily_fee=%d, zero_amount=%d)",
        len(created),
        len(updated),
        teacher_id,
        skipped_already_generated,
        skipped_no_daily_fee,
        skipped_zero_days,
    )

    return FeeGenerationSummaryResponse(
        created=created,
        updated=updated,
        skipped_already_generated=skipped_already_generated,
        skipped_no_daily_fee=skipped_no_daily_fee,
        skipped_zero_days=skipped_zero_days,
    )
