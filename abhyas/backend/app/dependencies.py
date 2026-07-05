"""Shared FastAPI dependencies: DB session, current-user resolution, RBAC."""
import logging
from collections.abc import Callable, Iterable

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.database import get_db as _get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# Re-exported so routers can `Depends(get_db)` from a single module.
get_db = _get_db


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the bearer JWT and load the corresponding active User.

    The access token is read from the `access_token` httpOnly cookie first
    (the primary transport for browser clients); the `Authorization: Bearer`
    header is used as a fallback for API tooling/tests when no cookie is set.

    Raises UnauthorizedError if the token is missing, invalid, expired, or the
    referenced user no longer exists / is inactive.
    """
    actual_token = request.cookies.get("access_token") or token
    if not actual_token:
        raise UnauthorizedError("Missing authentication token")

    payload = decode_token(actual_token)
    if not payload:
        logger.info("JWT decode failed for provided bearer token")
        raise UnauthorizedError("Invalid or expired token")

    if payload.get("type") not in (None, "access"):
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not getattr(user, "is_active", True):
        raise UnauthorizedError("User not found or inactive")

    return user


def require_role(*roles: str) -> Callable[[User], User]:
    """Dependency factory enforcing that the current user has one of `roles`.

    Usage:
        @router.get("/admin/stats", dependencies=[Depends(require_role("admin"))])
    """
    allowed: Iterable[str] = roles

    def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise ForbiddenError(
                f"Requires one of roles: {', '.join(allowed)}"
            )
        return current_user

    return _check_role
