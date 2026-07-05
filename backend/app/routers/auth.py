"""Authentication endpoints: register, login, refresh, logout, Google OAuth, profile."""
import logging
import secrets

from fastapi import APIRouter, Cookie, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.oauth import GoogleOAuthError, build_authorization_url, exchange_code_for_token, fetch_google_userinfo
from app.config import settings
from app.dependencies import get_current_user, get_db
from app.exceptions import UnauthorizedError
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import AuthAck, TokenResponse, UserRegister, UserResponse, UserUpdate
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_STATE_COOKIE = "google_oauth_state"
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"


def _google_redirect_uri() -> str:
    """The backend's own callback URL - this is what must be registered with
    Google as an authorized redirect URI, since Google sends the auth code
    here (not to the frontend). We then redirect the browser to the frontend
    once the code has been exchanged and the auth cookies have been set.
    """
    return f"{settings.VITE_API_URL.rstrip('/')}/api/v1/auth/google/callback"


def _set_auth_cookies(response: Response, tokens: TokenResponse) -> None:
    """Set the access/refresh tokens as separate httpOnly cookies on `response`.

    Cookies (not the JSON body or URL) are the sole transport for tokens -
    this keeps them out of reach of XSS-driven JS and browser history/logs.
    """
    secure = settings.ENVIRONMENT != "development"
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=tokens.access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=tokens.refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, payload: UserRegister, db: Session = Depends(get_db)) -> User:
    """Self-signup for teachers. Parent/admin accounts cannot be created here."""
    return auth_service.register_user(db, payload)


@router.post("/login", response_model=AuthAck)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> AuthAck:
    """Login with email (as `username`) and password, OAuth2 password-flow form encoded.

    Tokens are set as httpOnly cookies on `response`; the body only confirms success.
    """
    tokens = auth_service.login_user(db, email=form.username, password=form.password)
    _set_auth_cookies(response, tokens)
    return AuthAck()


@router.post("/refresh", response_model=AuthAck)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> AuthAck:
    """Exchange a valid, unrevoked refresh token (read from its cookie) for a new pair.

    Rotation: the used refresh token is revoked and the new pair is set as cookies.
    """
    if not refresh_token:
        raise UnauthorizedError("Missing refresh token")
    tokens = auth_service.refresh_access_token(db, refresh_token)
    _set_auth_cookies(response, tokens)
    return AuthAck()


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> None:
    """Revoke the caller's refresh token (from its cookie) and clear both auth cookies."""
    if refresh_token:
        auth_service.logout_user(db, refresh_token)
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/")


@router.get("/google")
async def google_login() -> RedirectResponse:
    """Redirect the browser to Google's OAuth consent screen.

    A random `state` value is generated, set as an httponly cookie, and echoed
    back by Google on callback - this is verified to prevent CSRF.
    """
    state = secrets.token_urlsafe(32)
    redirect = RedirectResponse(url=build_authorization_url(state, _google_redirect_uri()))
    redirect.set_cookie(
        key=GOOGLE_STATE_COOKIE,
        value=state,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=600,
    )
    return redirect


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    google_oauth_state: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Handle Google's redirect: verify CSRF state, exchange code, upsert user, issue tokens."""
    if not google_oauth_state or not secrets.compare_digest(state, google_oauth_state):
        raise UnauthorizedError("Invalid or missing OAuth state parameter")

    try:
        token_data = await exchange_code_for_token(code, _google_redirect_uri())
        userinfo = await fetch_google_userinfo(token_data["access_token"])
    except GoogleOAuthError as exc:
        logger.warning("Google OAuth callback failed: %s", exc)
        raise UnauthorizedError("Google authentication failed") from exc

    email = userinfo.get("email")
    if not email:
        raise UnauthorizedError("Google account did not return an email address")

    user = auth_service.get_or_create_oauth_user(
        db,
        email=email,
        full_name=userinfo.get("name", email),
        provider="google",
    )
    tokens = auth_service.issue_token_pair(db, user)

    redirect_url = f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback"
    response = RedirectResponse(url=redirect_url)
    _set_auth_cookies(response, tokens)
    response.delete_cookie(GOOGLE_STATE_COOKIE)
    return response


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Update self-editable profile fields for the current user."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
        db.commit()
        db.refresh(current_user)
    return current_user
