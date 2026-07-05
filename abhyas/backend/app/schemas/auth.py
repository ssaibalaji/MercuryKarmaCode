"""Pydantic schemas for the authentication module."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserRegister(BaseModel):
    """Payload for teacher self-signup. Parents/admins cannot self-register.

    `extra="forbid"` ensures a client cannot smuggle a `role` field (or any
    other field) into the request body - registration always creates a
    `teacher` account. Parent accounts are created via the invite flow only.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)


class UserLogin(BaseModel):
    """Payload for email/password login (used by non-form clients, e.g. tests)."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Access + refresh token pair. Used internally between the service and
    router layers only - the tokens are set as httpOnly cookies by the router
    and never serialized into a JSON response body (see AuthAck).
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthAck(BaseModel):
    """Minimal JSON body returned by login/refresh once tokens have been set
    as httpOnly cookies - confirms success without exposing the tokens.
    """

    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public-facing representation of a User."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    oauth_provider: str | None = None


class UserUpdate(BaseModel):
    """Payload for PUT /auth/me - only self-editable fields."""

    full_name: str | None = Field(default=None, min_length=1, max_length=150)
