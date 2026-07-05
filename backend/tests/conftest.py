"""Shared pytest fixtures: throwaway SQLite DB + FastAPI TestClient."""
import os
from collections.abc import Generator

# Ensure required settings are present before any `app.*` module is imported
# (Settings.SECRET_KEY has no default). Local/CI environments may already
# provide these via a real .env; setdefault avoids clobbering that.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.jwt import create_access_token, hash_password
from app.database import Base, get_db
from app.dependencies import get_db as deps_get_db
from app.main import app
from app.models.user import User, UserRole
from app.rate_limit import limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> Generator[None, None, None]:
    """The slowapi Limiter keeps its counters in process memory, shared across
    the whole test session since `app` (and its limiter) is imported once.
    Reset before every test so one test's auth attempts never trip the limit
    in an unrelated test.
    """
    limiter.reset()
    yield


@pytest.fixture()
def test_db() -> Generator[Session, None, None]:
    """A fresh in-memory SQLite database per test, with all tables created."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Import models so they're registered on Base.metadata before create_all.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """A TestClient with the get_db dependency overridden to use test_db."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield test_db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[deps_get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _create_user(db: Session, *, email: str, full_name: str, role: UserRole) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_headers_for(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def teacher_user(test_db: Session) -> User:
    return _create_user(
        test_db, email="teacher@example.com", full_name="Teacher One", role=UserRole.teacher
    )


@pytest.fixture()
def other_teacher_user(test_db: Session) -> User:
    return _create_user(
        test_db, email="other-teacher@example.com", full_name="Teacher Two", role=UserRole.teacher
    )


@pytest.fixture()
def parent_user(test_db: Session) -> User:
    return _create_user(
        test_db, email="parent@example.com", full_name="Parent One", role=UserRole.parent
    )


@pytest.fixture()
def admin_user(test_db: Session) -> User:
    return _create_user(
        test_db, email="admin@example.com", full_name="Admin One", role=UserRole.admin
    )


@pytest.fixture()
def auth_headers(teacher_user: User) -> dict[str, str]:
    """Auth headers for the default teacher fixture."""
    return _auth_headers_for(teacher_user)


@pytest.fixture()
def parent_auth_headers(parent_user: User) -> dict[str, str]:
    """Auth headers for the default parent fixture."""
    return _auth_headers_for(parent_user)


@pytest.fixture()
def other_teacher_auth_headers(other_teacher_user: User) -> dict[str, str]:
    """Auth headers for a second teacher, used for cross-tenant access tests."""
    return _auth_headers_for(other_teacher_user)


@pytest.fixture()
def admin_auth_headers(admin_user: User) -> dict[str, str]:
    """Auth headers for the default admin fixture."""
    return _auth_headers_for(admin_user)
