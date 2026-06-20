"""Tests for /auth endpoints: register, login, me, refresh."""
from app.auth.jwt import create_access_token
from app.models.refresh_token import RefreshToken


def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@test.com",
            "password": "password123",
            "full_name": "New User",
            "role": "student",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@test.com"
    assert body["role"] == "student"
    assert "id" in body
    # Password must never be echoed back.
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_conflict(client, test_student):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_student.email,
            "password": "anotherpassword",
            "role": "student",
        },
    )
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "CONFLICT"


def test_login_success(client, test_student):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_student.email, "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client, test_student):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_student.email, "password": "wrong-password"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "UNAUTHORIZED"


def test_login_unknown_email(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "doesnotexist@example.com", "password": "password123"},
    )
    assert response.status_code == 401


def test_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_authorized(client, test_student, student_auth_headers):
    response = client.get("/api/v1/auth/me", headers=student_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == test_student.email
    assert body["role"] == "student"


def test_me_invalid_token_rejected(client):
    headers = {"Authorization": "Bearer not-a-real-token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_refresh_token_rotation(client, db, test_student):
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_student.email, "password": "password123"},
    )
    old_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert refresh_response.status_code == 200
    body = refresh_response.json()
    assert "access_token" in body
    new_refresh_token = body["refresh_token"]
    assert new_refresh_token != old_refresh_token

    # The old refresh token must be revoked (rotation), so reusing it fails.
    old_record = (
        db.query(RefreshToken).filter(RefreshToken.token == old_refresh_token).first()
    )
    assert old_record is not None
    assert old_record.revoked is True

    reuse_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert reuse_response.status_code == 401

    # The newly issued refresh token should work.
    second_refresh_response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": new_refresh_token}
    )
    assert second_refresh_response.status_code == 200


def test_refresh_with_garbage_token_unauthorized(client):
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "garbage-token"}
    )
    assert response.status_code == 401


def test_refresh_with_access_token_rejected(client, test_student):
    # An access token (type="access") must not be usable as a refresh token.
    access_token = create_access_token({"sub": str(test_student.id)})
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": access_token}
    )
    assert response.status_code == 401
