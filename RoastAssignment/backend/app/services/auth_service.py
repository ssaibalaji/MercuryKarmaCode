"""Business logic for registration, login, and refresh-token lifecycle."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.exceptions import ConflictError, UnauthorizedError
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest


def register_user(db: Session, data: RegisterRequest) -> User:
    """Create a new local (email/password) user.

    Raises ConflictError if the email is already registered.
    """
    if db.query(User).filter(User.email == data.email).first():
        raise ConflictError("Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole(data.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Validate email/password credentials and return the matching active user.

    Raises UnauthorizedError if the credentials are invalid or the user has
    no local password (e.g. OAuth-only account).
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.hashed_password or not verify_password(
        password, user.hashed_password
    ):
        raise UnauthorizedError("Invalid email or password")
    return user


def get_or_create_google_user(db: Session, google_user_info: dict, role: str) -> User:
    """Find an existing user by google_id/email, or create one for first-time sign-in."""
    google_id = google_user_info.get("id") or google_user_info.get("sub")
    email = google_user_info.get("email")

    user = None
    if google_id:
        user = db.query(User).filter(User.google_id == google_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if user:
        # Backfill OAuth linkage for a user that previously registered locally.
        if not user.google_id and google_id:
            user.google_id = google_id
            user.oauth_provider = "google"
            db.commit()
            db.refresh(user)
        return user

    user = User(
        email=email,
        hashed_password=None,
        full_name=google_user_info.get("name"),
        role=UserRole(role),
        is_verified=bool(google_user_info.get("verified_email", True)),
        oauth_provider="google",
        google_id=google_id,
        avatar_url=google_user_info.get("picture"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_refresh_token_record(
    db: Session, user_id: int, token: str, expires_at: datetime
) -> RefreshToken:
    """Persist a refresh token so it can later be validated/revoked."""
    record = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def revoke_refresh_token(db: Session, token: str) -> None:
    """Mark a refresh token as revoked (no-op if it doesn't exist)."""
    record = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if record:
        record.revoked = True
        db.commit()


def rotate_refresh_token(db: Session, old_token: str) -> tuple[str, str]:
    """Validate `old_token`, then issue and persist a new access/refresh pair.

    Raises UnauthorizedError if the token is malformed, unknown, revoked, or
    expired (whether by JWT exp claim or by the persisted expires_at).
    """
    payload = decode_token(old_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    record = db.query(RefreshToken).filter(RefreshToken.token == old_token).first()
    if not record or record.revoked:
        raise UnauthorizedError("Refresh token revoked or unknown")

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token expired")

    user_id = payload.get("sub")
    user: Optional[User] = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    record.revoked = True
    db.add(record)

    new_expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    db.add(
        RefreshToken(
            user_id=user.id, token=new_refresh_token, expires_at=new_expires_at
        )
    )
    db.commit()

    return new_access_token, new_refresh_token
