"""Tests for the admin panel endpoints."""
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt import hash_password
from app.models.student import Student
from app.models.user import User, UserRole


def test_list_users_as_admin(
    client: TestClient, admin_auth_headers: dict[str, str], teacher_user: User, parent_user: User
) -> None:
    response = client.get("/api/v1/admin/users", headers=admin_auth_headers)

    assert response.status_code == 200
    emails = {user["email"] for user in response.json()}
    assert teacher_user.email in emails
    assert parent_user.email in emails


def test_list_users_denied_for_non_admin(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/admin/users", headers=auth_headers)

    assert response.status_code == 403


def test_list_users_denied_without_auth(client: TestClient) -> None:
    response = client.get("/api/v1/admin/users")

    assert response.status_code == 401


def test_update_user_as_admin(
    client: TestClient, admin_auth_headers: dict[str, str], teacher_user: User
) -> None:
    response = client.put(
        f"/api/v1/admin/users/{teacher_user.id}",
        headers=admin_auth_headers,
        json={"is_active": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["role"] == "teacher"


def test_update_user_role(
    client: TestClient, admin_auth_headers: dict[str, str], parent_user: User
) -> None:
    response = client.put(
        f"/api/v1/admin/users/{parent_user.id}",
        headers=admin_auth_headers,
        json={"role": "teacher"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "teacher"


def test_update_user_not_found(client: TestClient, admin_auth_headers: dict[str, str]) -> None:
    response = client.put(
        "/api/v1/admin/users/99999",
        headers=admin_auth_headers,
        json={"is_active": False},
    )

    assert response.status_code == 404


def test_update_user_denied_for_non_admin(
    client: TestClient, auth_headers: dict[str, str], parent_user: User
) -> None:
    response = client.put(
        f"/api/v1/admin/users/{parent_user.id}",
        headers=auth_headers,
        json={"is_active": False},
    )

    assert response.status_code == 403


def test_platform_stats_as_admin(
    client: TestClient,
    test_db: Session,
    admin_auth_headers: dict[str, str],
    teacher_user: User,
    parent_user: User,
) -> None:
    student = Student(
        teacher_id=teacher_user.id,
        full_name="Kid",
        date_of_birth=date(2016, 1, 1),
        class_grade="3",
        enrollment_date=date(2024, 1, 1),
        is_active=True,
    )
    test_db.add(student)
    test_db.commit()

    response = client.get("/api/v1/admin/stats", headers=admin_auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_teachers"] >= 1
    assert data["total_parents"] >= 1
    assert data["total_students"] == 1
    assert data["total_users"] >= 3  # admin + teacher + parent


def test_platform_stats_denied_for_non_admin(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/admin/stats", headers=auth_headers)

    assert response.status_code == 403


def test_update_user_blocks_demoting_last_active_admin(
    client: TestClient, admin_auth_headers: dict[str, str], admin_user: User
) -> None:
    response = client.put(
        f"/api/v1/admin/users/{admin_user.id}",
        headers=admin_auth_headers,
        json={"role": "teacher"},
    )

    assert response.status_code == 409


def test_update_user_blocks_deactivating_last_active_admin(
    client: TestClient, admin_auth_headers: dict[str, str], admin_user: User
) -> None:
    response = client.put(
        f"/api/v1/admin/users/{admin_user.id}",
        headers=admin_auth_headers,
        json={"is_active": False},
    )

    assert response.status_code == 409


def test_update_user_allows_demoting_admin_when_another_active_admin_exists(
    client: TestClient, admin_auth_headers: dict[str, str], admin_user: User, test_db: Session
) -> None:
    other_admin = User(
        email="admin2@example.com",
        hashed_password=hash_password("Password123!"),
        full_name="Admin Two",
        role=UserRole.admin,
        is_active=True,
        is_verified=True,
    )
    test_db.add(other_admin)
    test_db.commit()

    response = client.put(
        f"/api/v1/admin/users/{admin_user.id}",
        headers=admin_auth_headers,
        json={"role": "teacher"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "teacher"
