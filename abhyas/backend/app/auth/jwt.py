"""Password hashing and JWT access/refresh token helpers."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# Passwords are hashed with the `bcrypt` library directly (not via passlib's
# CryptContext) because passlib 1.7.x's backend version-sniffing is broken
# against bcrypt>=4.1 (it looks for a removed `__about__.__version__`
# attribute). bcrypt itself truncates/rejects secrets over 72 bytes, so we
# encode and truncate defensively before hashing.
_MAX_BCRYPT_BYTES = 72


def _prepare(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_BCRYPT_BYTES]


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    hashed = bcrypt.hashpw(_prepare(password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(_prepare(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict[str, Any]) -> str:
    """Create a short-lived JWT access token embedding `data` (typically {"sub": user_id})."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {**data, "exp": expire, "type": "access", "jti": uuid.uuid4().hex}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a long-lived JWT refresh token embedding `data` (typically {"sub": user_id}).

    Includes a random `jti` claim so two tokens minted for the same user within
    the same second are never byte-identical - refresh tokens are stored
    uniquely in the database, so a collision would otherwise raise an
    IntegrityError on rapid successive refreshes.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {**data, "exp": expire, "type": "refresh", "jti": uuid.uuid4().hex}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT, returning its payload or None if invalid/expired."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
