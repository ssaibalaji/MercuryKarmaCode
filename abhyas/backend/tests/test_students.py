"""Tests for the Students module: CRUD happy paths + role-based access control."""
from fastapi.testclient import TestClient

from app.models.user import User

STUDENTS_URL = "/api/v1/students"


def _student_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "full_name": "Asha Rao",
        "date_of_birth": "2012-05-10",
        "class_grade": "7",
        "section": "A",
        "roll_number": "07",
        "photo_url": None,
        "parent_name": "Rita Rao",
        "parent_email": "rita.rao@example.com",
        "parent_phone": "+911234567890",
        "enrollment_date": "2023-06-01",
    }
    payload.update(overrides)
    return payload


def test_teacher_can_create_student(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(STUDENTS_URL, json=_student_payload(), headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Asha Rao"
    assert body["is_active"] is True
    assert body["parent_user_id"] is None


def test_teacher_can_list_own_students(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.post(STUDENTS_URL, json=_student_payload(), headers=auth_headers)
    client.post(
        STUDENTS_URL, json=_student_payload(full_name="Second Student"), headers=auth_headers
    )

    response = client.get(STUDENTS_URL, headers=auth_headers)
    assert response.status_code == 200
    names = {item["full_name"] for item in response.json()}
    assert names == {"Asha Rao", "Second Student"}


def test_teacher_can_get_update_and_deactivate_own_student(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post(
        STUDENTS_URL, json=_student_payload(), headers=auth_headers
    ).json()
    student_id = created["id"]

    get_response = client.get(f"{STUDENTS_URL}/{student_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["full_name"] == "Asha Rao"

    update_response = client.put(
        f"{STUDENTS_URL}/{student_id}",
        json={"full_name": "Asha Rao Updated", "section": "B"},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Asha Rao Updated"
    assert update_response.json()["section"] == "B"

    delete_response = client.delete(f"{STUDENTS_URL}/{student_id}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False


def test_get_nonexistent_student_returns_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get(f"{STUDENTS_URL}/999999", headers=auth_headers)
    assert response.status_code == 404


def test_parent_cannot_create_student(
    client: TestClient, parent_auth_headers: dict[str, str]
) -> None:
    response = client.post(STUDENTS_URL, json=_student_payload(), headers=parent_auth_headers)
    assert response.status_code == 403


def test_parent_cannot_update_student(
    client: TestClient,
    auth_headers: dict[str, str],
    parent_auth_headers: dict[str, str],
) -> None:
    created = client.post(
        STUDENTS_URL, json=_student_payload(), headers=auth_headers
    ).json()
    student_id = created["id"]

    response = client.put(
        f"{STUDENTS_URL}/{student_id}",
        json={"full_name": "Hacked Name"},
        headers=parent_auth_headers,
    )
    assert response.status_code == 403


def test_parent_cannot_delete_student(
    client: TestClient,
    auth_headers: dict[str, str],
    parent_auth_headers: dict[str, str],
) -> None:
    created = client.post(
        STUDENTS_URL, json=_student_payload(), headers=auth_headers
    ).json()
    student_id = created["id"]

    response = client.delete(f"{STUDENTS_URL}/{student_id}", headers=parent_auth_headers)
    assert response.status_code == 403


def test_teacher_cannot_see_another_teachers_student(
    client: TestClient,
    auth_headers: dict[str, str],
    other_teacher_auth_headers: dict[str, str],
) -> None:
    created = client.post(
        STUDENTS_URL, json=_student_payload(), headers=auth_headers
    ).json()
    student_id = created["id"]

    # Not in the other teacher's list.
    list_response = client.get(STUDENTS_URL, headers=other_teacher_auth_headers)
    assert list_response.status_code == 200
    assert all(item["id"] != student_id for item in list_response.json())

    # Direct fetch is forbidden.
    get_response = client.get(f"{STUDENTS_URL}/{student_id}", headers=other_teacher_auth_headers)
    assert get_response.status_code == 403

    # Update/delete are forbidden too.
    update_response = client.put(
        f"{STUDENTS_URL}/{student_id}",
        json={"full_name": "Nope"},
        headers=other_teacher_auth_headers,
    )
    assert update_response.status_code == 403

    delete_response = client.delete(
        f"{STUDENTS_URL}/{student_id}", headers=other_teacher_auth_headers
    )
    assert delete_response.status_code == 403


def test_parent_can_see_linked_student_but_not_unlinked(
    client: TestClient,
    auth_headers: dict[str, str],
    parent_auth_headers: dict[str, str],
    parent_user: User,
    test_db,
) -> None:
    from app.models.student import Student

    created = client.post(
        STUDENTS_URL, json=_student_payload(), headers=auth_headers
    ).json()
    student_id = created["id"]

    # Not yet linked -> parent cannot see it.
    response = client.get(f"{STUDENTS_URL}/{student_id}", headers=parent_auth_headers)
    assert response.status_code == 403

    # Link the student to the parent directly (simulating a completed invite).
    student = test_db.query(Student).filter(Student.id == student_id).first()
    student.parent_user_id = parent_user.id
    test_db.commit()

    response = client.get(f"{STUDENTS_URL}/{student_id}", headers=parent_auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == student_id

    list_response = client.get(STUDENTS_URL, headers=parent_auth_headers)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [student_id]


def test_invite_parent_links_existing_parent_account(
    client: TestClient,
    auth_headers: dict[str, str],
    parent_user: User,
) -> None:
    created = client.post(
        STUDENTS_URL, json=_student_payload(), headers=auth_headers
    ).json()
    student_id = created["id"]

    response = client.post(
        f"{STUDENTS_URL}/{student_id}/invite-parent",
        json={"parent_email": parent_user.email, "parent_name": "Parent One"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["invited"] is True
    assert body["parent_user_id"] == parent_user.id


def test_invite_parent_without_existing_account_leaves_unlinked(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post(
        STUDENTS_URL, json=_student_payload(), headers=auth_headers
    ).json()
    student_id = created["id"]

    response = client.post(
        f"{STUDENTS_URL}/{student_id}/invite-parent",
        json={"parent_email": "not-registered@example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["invited"] is True
    assert body["parent_user_id"] is None


def test_parent_cannot_invite_parent(
    client: TestClient,
    auth_headers: dict[str, str],
    parent_auth_headers: dict[str, str],
) -> None:
    created = client.post(
        STUDENTS_URL, json=_student_payload(), headers=auth_headers
    ).json()
    student_id = created["id"]

    response = client.post(
        f"{STUDENTS_URL}/{student_id}/invite-parent",
        json={"parent_email": "someone@example.com"},
        headers=parent_auth_headers,
    )
    assert response.status_code == 403


def test_unauthenticated_request_is_rejected(client: TestClient) -> None:
    response = client.get(STUDENTS_URL)
    assert response.status_code == 401
