"""Pydantic schemas for the Students module."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr

ScheduledDay = Literal["sun", "mon", "tue", "wed", "thu", "fri", "sat"]


class StudentBase(BaseModel):
    """Fields shared by create/update payloads."""

    full_name: str
    date_of_birth: date
    class_grade: str
    section: str | None = None
    roll_number: str | None = None
    photo_url: str | None = None
    parent_name: str | None = None
    parent_email: EmailStr | None = None
    parent_phone: str | None = None
    enrollment_date: date
    daily_fee: Decimal | None = None
    scheduled_days: list[ScheduledDay] = []
    monthly_fee: Decimal | None = None


class StudentCreate(StudentBase):
    """Payload for creating a student. teacher_id is derived from the current user."""


class StudentUpdate(BaseModel):
    """Payload for updating a student. All fields optional (partial update)."""

    full_name: str | None = None
    date_of_birth: date | None = None
    class_grade: str | None = None
    section: str | None = None
    roll_number: str | None = None
    photo_url: str | None = None
    parent_name: str | None = None
    parent_email: EmailStr | None = None
    parent_phone: str | None = None
    enrollment_date: date | None = None
    is_active: bool | None = None
    daily_fee: Decimal | None = None
    scheduled_days: list[ScheduledDay] | None = None
    monthly_fee: Decimal | None = None


class StudentResponse(StudentBase):
    """Full student representation returned by detail/create/update endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_id: int
    parent_user_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StudentListItem(BaseModel):
    """Lighter-weight representation used for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    class_grade: str
    section: str | None
    roll_number: str | None
    photo_url: str | None
    is_active: bool
    parent_user_id: int | None
    daily_fee: Decimal | None = None
    scheduled_days: list[ScheduledDay] = []
    monthly_fee: Decimal | None = None


class ParentInviteRequest(BaseModel):
    """Request body for inviting a parent to link to a student."""

    parent_email: EmailStr
    parent_name: str | None = None


class ParentInviteResponse(BaseModel):
    """Response describing the outcome of a parent invite request."""

    student_id: int
    parent_email: EmailStr
    invited: bool
    parent_user_id: int | None
    message: str


class MonthlyFeePreviewResponse(BaseModel):
    """Preview of the calculated monthly fee for an arbitrary month, without
    persisting anything to the student's stored monthly_fee."""

    year: int
    month: int
    calculated_monthly_fee: str
