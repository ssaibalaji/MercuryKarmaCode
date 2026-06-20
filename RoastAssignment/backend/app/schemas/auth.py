"""Pydantic schemas for authentication endpoints."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, field_validator


class Token(BaseModel):
    """Access/refresh token pair returned on login, refresh, and OAuth callback."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    """Payload for self-registration via email/password."""

    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Literal["student", "examiner", "coach"]


class RefreshRequest(BaseModel):
    """Payload for refreshing or revoking a refresh token."""

    refresh_token: str


class GoogleCallbackRequest(BaseModel):
    """Payload the SPA sends after Google redirects it to /auth/callback."""

    code: str
    state: str


class UserUpdateRequest(BaseModel):
    """Payload for updating the current user's profile."""

    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Public-facing representation of a user."""

    id: int
    email: EmailStr
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("role", mode="before")
    @classmethod
    def _coerce_role(cls, value: object) -> str:
        """Accept the SQLAlchemy `UserRole` enum member and coerce to its value."""
        return value.value if hasattr(value, "value") else value
