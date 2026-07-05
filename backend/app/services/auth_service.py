"""Business logic for registration, login, token refresh, logout, and OAuth."""
from datetime import datetime, timedelta, timezone

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
from app.models.user import User, UserRole
from app.models.user import RefreshToken
from app.schemas.auth import TokenResponse, UserRegister


def issue_token_pair(db: Session, user: User) -> TokenResponse:
    """Create a new access/refresh token pair and persist the refresh token."""
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user.id, token=refresh_token, expires_at=expires_at, revoked=False))
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def register_user(db: Session, payload: UserRegister) -> User:
    """Register a new teacher account. Raises ConflictError if the email is taken."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise ConflictError("An account with this email already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.teacher,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Verify email/password credentials. Raises UnauthorizedError on failure."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise UnauthorizedError("This account has been deactivated")
    return user


def login_user(db: Session, email: str, password: str) -> TokenResponse:
    """Authenticate a user and issue a fresh token pair."""
    user = authenticate_user(db, email, password)
    return issue_token_pair(db, user)


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    """Validate a refresh token and issue a new token pair (refresh token rotation)."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    stored = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not stored:
        raise UnauthorizedError("Refresh token not recognized")
    if stored.revoked:
        raise UnauthorizedError("Refresh token has been revoked")

    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token has expired")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    # Rotate: revoke the used refresh token and issue a new pair.
    stored.revoked = True
    db.commit()

    return issue_token_pair(db, user)


def logout_user(db: Session, refresh_token: str) -> None:
    """Revoke a refresh token so it can no longer be used to mint access tokens."""
    stored = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if stored and not stored.revoked:
        stored.revoked = True
        db.commit()


def get_or_create_oauth_user(db: Session, *, email: str, full_name: str, provider: str) -> User:
    """Fetch an existing user by email or create a new teacher account for OAuth sign-in."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        if not user.oauth_provider:
            user.oauth_provider = provider
            db.commit()
            db.refresh(user)
        return user

    user = User(
        email=email,
        hashed_password=None,
        full_name=full_name or email,
        role=UserRole.teacher,
        is_active=True,
        is_verified=True,
        oauth_provider=provider,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
