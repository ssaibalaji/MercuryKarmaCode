"""Shared pytest fixtures for the backend test suite.

ADAPTATION FROM skills/TESTING.md: the skill's documented `db` fixture points
at a live Postgres test database (`postgresql://test:test@localhost/test_db`).
That's not guaranteed to be available in every environment these tests run
in (e.g. CI without a Postgres service container, or a fresh dev box), so this
conftest swaps in a SQLite in-memory engine (`sqlite:///:memory:`) instead.

To make the in-memory DB survive across the multiple connections SQLAlchemy
may open per test (a real concern with `sqlite://:memory:`, which is normally
private per-connection), we use `StaticPool` with `check_same_thread=False` so
every `SessionLocal()`/`TestSession()` call reuses the same underlying
connection. This also matters for `run_evaluation_for_submission`, which opens
its own session via `app.database.SessionLocal` (see test_evaluation_service.py) -
that session must see the same in-memory database as the request-scoped
`db` fixture.
"""
import os

# `app.config.Settings` requires DATABASE_URL and SECRET_KEY with no defaults
# (see app/config.py). These must be set BEFORE any `app.*` module is
# imported (importing app.config eagerly instantiates `settings = Settings()`
# at module scope), so set sane test defaults here, before the imports below.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.jwt import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole

TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture
def db():
    """Create all tables, yield a session, then drop all tables.

    Also monkeypatches `app.database.SessionLocal` for the duration of the
    test so background-task code (e.g. `run_evaluation_for_submission`, which
    opens its own session via `SessionLocal()` rather than the request-scoped
    `get_db` dependency) reads/writes the same in-memory SQLite database
    instead of trying to hit the real `DATABASE_URL`.
    """
    Base.metadata.create_all(bind=engine)
    session = TestSession()

    # `app.database.SessionLocal` is imported by name (`from app.database
    # import SessionLocal`) in several modules that open their own session
    # outside the request lifecycle (e.g. `app.services.evaluation_service`,
    # `app.scheduler`). Patching the attribute on `app.database` alone would
    # NOT affect those already-bound local references, so patch each
    # importing module's own `SessionLocal` name too, pointing all of them at
    # our StaticPool-backed `TestSession` (same in-memory connection as the
    # `db` fixture's session).
    import app.database as database_module
    import app.services.evaluation_service as evaluation_service_module
    import app.scheduler as scheduler_module

    patched_modules = [database_module, evaluation_service_module, scheduler_module]
    originals = [m.SessionLocal for m in patched_modules]
    for m in patched_modules:
        m.SessionLocal = TestSession

    try:
        yield session
    finally:
        session.close()
        for m, original in zip(patched_modules, originals):
            m.SessionLocal = original
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_student(db):
    user = User(
        email="student@example.com",
        hashed_password=hash_password("password123"),
        full_name="Stu Dent",
        role=UserRole.student,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_examiner(db):
    user = User(
        email="examiner@example.com",
        hashed_password=hash_password("password123"),
        full_name="Exam Iner",
        role=UserRole.examiner,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_coach(db):
    user = User(
        email="coach@example.com",
        hashed_password=hash_password("password123"),
        full_name="Coach Carter",
        role=UserRole.coach,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student_auth_headers(test_student):
    token = create_access_token({"sub": str(test_student.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def examiner_auth_headers(test_examiner):
    token = create_access_token({"sub": str(test_examiner.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def coach_auth_headers(test_coach):
    token = create_access_token({"sub": str(test_coach.id)})
    return {"Authorization": f"Bearer {token}"}
