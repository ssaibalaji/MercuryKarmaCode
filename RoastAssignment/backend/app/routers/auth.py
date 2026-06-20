"""Authentication endpoints: register, login, refresh, logout, Google OAuth, profile."""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token, create_refresh_token
from app.auth.oauth import get_google_tokens, get_google_user
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.limiter import limiter
from app.models.user import User
from app.schemas.auth import (
    RefreshRequest,
    RegisterRequest,
    Token,
    UserResponse,
    UserUpdateRequest,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_OAUTH_STATE_COOKIE = "oauth_state"


def _issue_token_pair(db: Session, user: User) -> Token:
    """Create an access/refresh pair for `user` and persist the refresh token."""
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    auth_service.create_refresh_token_record(db, user.id, refresh_token, expires_at)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request, data: RegisterRequest, db: Session = Depends(get_db)
) -> User:
    """Register a new local (email/password) user."""
    return auth_service.register_user(db, data)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate with email/password (form.username = email) and issue tokens."""
    user = auth_service.authenticate_user(db, form.username, form.password)
    return _issue_token_pair(db, user)


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
async def refresh(
    request: Request, data: RefreshRequest, db: Session = Depends(get_db)
) -> Token:
    """Rotate a refresh token: revoke the old one, issue a new access/refresh pair."""
    access_token, refresh_token = auth_service.rotate_refresh_token(
        db, data.refresh_token
    )
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, db: Session = Depends(get_db)) -> None:
    """Revoke a refresh token, logging the holder out of that session."""
    auth_service.revoke_refresh_token(db, data.refresh_token)


@router.get("/google")
async def google_login() -> RedirectResponse:
    """Redirect the browser to Google's OAuth consent screen.

    Generates a random `state` token, stores it in a short-lived httpOnly
    cookie, and includes it in the Google auth URL so the callback can verify
    the request originated here (CSRF protection per RFC 6749 §10.12).

    Returns 503 if Google OAuth is not configured (no GOOGLE_CLIENT_ID set).
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured",
        )

    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{settings.FRONTEND_URL}/auth/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    response = RedirectResponse(
        url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}",
        status_code=status.HTTP_302_FOUND,
    )
    is_secure = settings.FRONTEND_URL.startswith("https")
    response.set_cookie(
        key=_OAUTH_STATE_COOKIE,
        value=state,
        httponly=True,
        secure=is_secure,  # False on http://localhost, True in production
        samesite="lax",
        max_age=300,  # 5 minutes — more than enough for a consent screen
    )
    return response


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    oauth_state: Optional[str] = Cookie(None),
    role: str = "student",
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Handle Google's redirect back with an authorization code.

    Verifies the `state` parameter matches the value we set in the
    `oauth_state` cookie to prevent CSRF attacks. Then exchanges the code,
    fetches the Google profile, finds-or-creates the local user, issues our
    own access/refresh tokens, and redirects to the frontend callback page.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured",
        )

    # Constant-time comparison prevents timing attacks on the state token.
    if not oauth_state or not secrets.compare_digest(state, oauth_state):
        logger.warning(
            "Google OAuth CSRF check failed: state mismatch (cookie=%r, param=%r)",
            oauth_state,
            state,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter",
        )

    google_tokens = await get_google_tokens(code)
    google_access_token = google_tokens.get("access_token")
    if not google_access_token:
        logger.warning("Google token exchange failed: %s", google_tokens)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed",
        )

    google_user_info = await get_google_user(google_access_token)
    user = auth_service.get_or_create_google_user(db, google_user_info, role)
    tokens = _issue_token_pair(db, user)

    redirect_params = urlencode(
        {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
        }
    )
    response = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback?{redirect_params}",
        status_code=status.HTTP_302_FOUND,
    )
    # Clear the state cookie — it's been consumed.
    response.delete_cookie(key=_OAUTH_STATE_COOKIE)
    return response


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Update mutable fields (currently full_name) on the authenticated user's profile."""
    if data.full_name is not None:
        user.full_name = data.full_name
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
