"""Tests for the authentication module: register, login, refresh, /me, RBAC."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt import create_refresh_token, hash_password
from app.models.user import RefreshToken, User, UserRole


def test_register_creates_teacher(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new.teacher@example.com", "password": "StrongPass123", "full_name": "New Teacher"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.teacher@example.com"
    assert body["role"] == "teacher"
    assert "hashed_password" not in body


def test_register_duplicate_email_conflicts(client: TestClient, teacher_user: User) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": teacher_user.email, "password": "StrongPass123", "full_name": "Dup"},
    )
    assert response.status_code == 409


def test_register_rejects_role_field(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "sneaky@example.com",
            "password": "StrongPass123",
            "full_name": "Sneaky",
            "role": "admin",
        },
    )
    assert response.status_code == 422


def test_login_success(client: TestClient, teacher_user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": teacher_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {"token_type": "bearer"}
    assert "access_token" not in body
    assert "refresh_token" not in body


def test_login_sets_httponly_cookies(client: TestClient, teacher_user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": teacher_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    set_cookie_headers = response.headers.get_list("set-cookie")
    access_cookie = next(h for h in set_cookie_headers if h.startswith("access_token="))
    refresh_cookie = next(h for h in set_cookie_headers if h.startswith("refresh_token="))
    assert "HttpOnly" in access_cookie
    assert "samesite=lax" in access_cookie.lower()
    assert "HttpOnly" in refresh_cookie
    assert "samesite=lax" in refresh_cookie.lower()

    # A subsequent request authenticates from the cookie jar alone - no
    # Authorization header is ever sent.
    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == teacher_user.email


def test_login_rate_limited_after_too_many_attempts(client: TestClient, teacher_user: User) -> None:
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            data={"username": teacher_user.email, "password": "wrong-password"},
        )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": teacher_user.email, "password": "wrong-password"},
    )
    assert response.status_code == 429


def test_login_bad_password_returns_401(client: TestClient, teacher_user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": teacher_user.email, "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ghost@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


def test_get_me_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_returns_current_user(client: TestClient, auth_headers: dict[str, str], teacher_user: User) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == teacher_user.email


def test_update_me_changes_full_name(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.put("/api/v1/auth/me", headers=auth_headers, json={"full_name": "Updated Name"})
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_refresh_rotates_token(client: TestClient, teacher_user: User, test_db: Session) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": teacher_user.email, "password": "Password123!"},
    )
    old_refresh_token = login_response.cookies["refresh_token"]

    # The client's cookie jar retains the refresh_token cookie from login, so
    # no body/param is needed - the endpoint reads it straight from the cookie.
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    assert response.json() == {"token_type": "bearer"}
    new_refresh_token = response.cookies["refresh_token"]
    assert new_refresh_token != old_refresh_token

    # The original refresh token must now be revoked and unusable.
    replay = client.post("/api/v1/auth/refresh", cookies={"refresh_token": old_refresh_token})
    assert replay.status_code == 401


def test_refresh_with_revoked_token_fails(client: TestClient, teacher_user: User, test_db: Session) -> None:
    token = create_refresh_token({"sub": str(teacher_user.id)})
    test_db.add(
        RefreshToken(
            user_id=teacher_user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked=True,
        )
    )
    test_db.commit()

    response = client.post("/api/v1/auth/refresh", cookies={"refresh_token": token})
    assert response.status_code == 401


def test_refresh_with_expired_token_fails(client: TestClient, teacher_user: User, test_db: Session) -> None:
    token = create_refresh_token({"sub": str(teacher_user.id)})
    test_db.add(
        RefreshToken(
            user_id=teacher_user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            revoked=False,
        )
    )
    test_db.commit()

    response = client.post("/api/v1/auth/refresh", cookies={"refresh_token": token})
    assert response.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient, teacher_user: User) -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": teacher_user.email, "password": "Password123!"},
    )
    refresh_token = login_response.cookies["refresh_token"]

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    reuse = client.post("/api/v1/auth/refresh", cookies={"refresh_token": refresh_token})
    assert reuse.status_code == 401


def test_require_role_blocks_non_admin(client: TestClient, auth_headers: dict[str, str]) -> None:
    # /admin/* is gated by require_role("admin") - a teacher must be forbidden.
    response = client.get("/api/v1/admin/users", headers=auth_headers)
    assert response.status_code == 403


def test_require_role_allows_admin(client: TestClient, test_db: Session) -> None:
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Admin One",
        role=UserRole.admin,
        is_active=True,
        is_verified=True,
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)

    from app.auth.jwt import create_access_token

    headers = {"Authorization": f"Bearer {create_access_token({'sub': str(admin.id)})}"}
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
