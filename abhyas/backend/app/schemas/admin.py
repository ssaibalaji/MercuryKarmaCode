"""Pydantic schemas for the admin panel module."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class AdminUserResponse(BaseModel):
    """Admin-facing representation of a platform user account."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class AdminUserUpdateRequest(BaseModel):
    """Payload for PUT /admin/users/{id} - admin-editable account fields."""

    is_active: bool | None = None
    role: UserRole | None = None


class AdminStatsResponse(BaseModel):
    """Platform-wide statistics shown on the admin dashboard."""

    total_users: int
    total_teachers: int
    total_parents: int
    total_students: int
    total_payments_this_month: float
