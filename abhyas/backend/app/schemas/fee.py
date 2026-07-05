"""Pydantic schemas for the Fees & Payments module."""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.fee import FeeFrequency, PaymentMethod, PaymentStatus


class FeeStructureBase(BaseModel):
    """Fields shared by fee structure create/update payloads."""

    amount: Decimal = Field(gt=0)
    frequency: FeeFrequency
    due_date: date
    description: str | None = None


class FeeStructureCreate(FeeStructureBase):
    """Payload for creating a fee structure. Teacher-only."""

    student_id: int


class FeeStructureUpdate(BaseModel):
    """Payload for updating a fee structure. All fields optional (partial update)."""

    amount: Decimal | None = Field(default=None, gt=0)
    frequency: FeeFrequency | None = None
    due_date: date | None = None
    description: str | None = None


class FeeStructureResponse(FeeStructureBase):
    """Full fee structure representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    created_at: datetime
    updated_at: datetime


class FeeStructureWithBalance(FeeStructureResponse):
    """A fee structure augmented with its computed outstanding balance."""

    student_name: str
    outstanding_balance: Decimal
    is_overdue: bool


class PaymentResponse(BaseModel):
    """Representation of a payment (pending/completed/failed)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fee_structure_id: int
    student_id: int
    amount_paid: Decimal
    payment_date: datetime
    method: PaymentMethod
    razorpay_payment_id: str | None
    razorpay_order_id: str | None
    status: PaymentStatus
    created_at: datetime


class FeeDetailResponse(BaseModel):
    """Fee structures + payment history + outstanding balance for one student."""

    student_id: int
    fee_structures: list[FeeStructureWithBalance]
    payments: list[PaymentResponse]
    total_outstanding: Decimal


class GeneratedFeeEntry(BaseModel):
    """A single fee structure auto-generated from attendance for one student/month."""

    student_id: int
    student_name: str
    year: int
    month: int
    amount: Decimal


class FeeGenerationSummaryResponse(BaseModel):
    """Summary of a `generate-from-attendance` run."""

    created: list[GeneratedFeeEntry]
    updated: list[GeneratedFeeEntry]
    skipped_already_generated: int
    skipped_no_daily_fee: int
    skipped_zero_days: int


class RazorpayOrderRequest(BaseModel):
    """Request body for creating a Razorpay order against a fee structure."""

    fee_structure_id: int


class RazorpayOrderResponse(BaseModel):
    """Response returned to the client to open Razorpay Checkout."""

    payment_id: int
    order_id: str
    amount: int
    currency: str
    key_id: str
