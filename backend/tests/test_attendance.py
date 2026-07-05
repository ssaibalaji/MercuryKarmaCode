"""Tests for the attendance module: marking/upsert, querying, summary, and RBAC."""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord
from app.models.student import Student
from app.models.user import User


@pytest.fixture()
def student(test_db: Session, teacher_user: User, parent_user: User) -> Student:
    """A student owned by `teacher_user` and linked to `parent_user`."""
    s = Student(
        teacher_id=teacher_user.id,
        full_name="Student One",
        date_of_birth=date(2012, 1, 1),
        class_grade="5",
        section="A",
        enrollment_date=date(2023, 6, 1),
        parent_user_id=parent_user.id,
        is_active=True,
    )
    test_db.add(s)
    test_db.commit()
    test_db.refresh(s)
    return s


@pytest.fixture()
def other_teacher_student(test_db: Session, other_teacher_user: User) -> Student:
    """A student owned by a different teacher - used for cross-tenant denial tests."""
    s = Student(
        teacher_id=other_teacher_user.id,
        full_name="Other Student",
        date_of_birth=date(2013, 2, 2),
        class_grade="6",
        enrollment_date=date(2023, 6, 1),
        is_active=True,
    )
    test_db.add(s)
    test_db.commit()
    test_db.refresh(s)
    return s


def _mark_payload(student_id: int, mark_date: str, status: str, notes: str | None = None) -> dict:
    entry: dict = {"student_id": student_id, "date": mark_date, "status": status}
    if notes is not None:
        entry["notes"] = notes
    return {"entries": [entry]}


class TestMarkAttendance:
    def test_mark_single_student_creates_record(
        self, client: TestClient, auth_headers: dict[str, str], student: Student
    ) -> None:
        resp = client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-01", "present"),
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert len(body) == 1
        assert body[0]["student_id"] == student.id
        assert body[0]["status"] == "present"
        assert body[0]["date"] == "2026-07-01"

    def test_bulk_mark_creates_multiple_records(
        self, client: TestClient, auth_headers: dict[str, str], test_db: Session, teacher_user: User
    ) -> None:
        s1 = Student(
            teacher_id=teacher_user.id,
            full_name="Bulk One",
            date_of_birth=date(2012, 1, 1),
            class_grade="5",
            enrollment_date=date(2023, 6, 1),
        )
        s2 = Student(
            teacher_id=teacher_user.id,
            full_name="Bulk Two",
            date_of_birth=date(2012, 1, 1),
            class_grade="5",
            enrollment_date=date(2023, 6, 1),
        )
        test_db.add_all([s1, s2])
        test_db.commit()
        test_db.refresh(s1)
        test_db.refresh(s2)

        payload = {
            "entries": [
                {"student_id": s1.id, "date": "2026-07-01", "status": "present"},
                {"student_id": s2.id, "date": "2026-07-01", "status": "absent", "notes": "sick"},
            ]
        }
        resp = client.post("/api/v1/attendance", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert len(body) == 2
        statuses = {item["student_id"]: item["status"] for item in body}
        assert statuses[s1.id] == "present"
        assert statuses[s2.id] == "absent"

    def test_remark_same_student_and_date_upserts_not_conflicts(
        self, client: TestClient, auth_headers: dict[str, str], student: Student, test_db: Session
    ) -> None:
        """Marking the same (student_id, date) twice should update in place, not 409."""
        first = client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-02", "absent"),
            headers=auth_headers,
        )
        assert first.status_code == 201
        first_id = first.json()[0]["id"]

        second = client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-02", "present", notes="arrived late morning fixed"),
            headers=auth_headers,
        )
        assert second.status_code == 201
        second_body = second.json()[0]
        assert second_body["id"] == first_id
        assert second_body["status"] == "present"

        # Exactly one row exists for this (student_id, date) pair.
        count = (
            test_db.query(AttendanceRecord)
            .filter(AttendanceRecord.student_id == student.id, AttendanceRecord.date == date(2026, 7, 2))
            .count()
        )
        assert count == 1

    def test_invalid_status_rejected(
        self, client: TestClient, auth_headers: dict[str, str], student: Student
    ) -> None:
        resp = client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-01", "excused"),
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_teacher_cannot_mark_another_teachers_student(
        self, client: TestClient, auth_headers: dict[str, str], other_teacher_student: Student
    ) -> None:
        resp = client.post(
            "/api/v1/attendance",
            json=_mark_payload(other_teacher_student.id, "2026-07-01", "present"),
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_parent_cannot_mark_attendance(
        self, client: TestClient, parent_auth_headers: dict[str, str], student: Student
    ) -> None:
        resp = client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-01", "present"),
            headers=parent_auth_headers,
        )
        assert resp.status_code == 403

    def test_unauthenticated_request_rejected(self, client: TestClient, student: Student) -> None:
        resp = client.post("/api/v1/attendance", json=_mark_payload(student.id, "2026-07-01", "present"))
        assert resp.status_code == 401


class TestUpdateAttendance:
    def test_teacher_updates_own_record(
        self, client: TestClient, auth_headers: dict[str, str], student: Student
    ) -> None:
        mark = client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-03", "absent"),
            headers=auth_headers,
        )
        record_id = mark.json()[0]["id"]

        resp = client.put(
            f"/api/v1/attendance/{record_id}",
            json={"status": "late", "notes": "traffic"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "late"
        assert resp.json()["notes"] == "traffic"

    def test_other_teacher_cannot_update(
        self, client: TestClient, auth_headers: dict[str, str], other_teacher_auth_headers: dict[str, str], student: Student
    ) -> None:
        mark = client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-03", "absent"),
            headers=auth_headers,
        )
        record_id = mark.json()[0]["id"]

        resp = client.put(
            f"/api/v1/attendance/{record_id}",
            json={"status": "present"},
            headers=other_teacher_auth_headers,
        )
        assert resp.status_code == 403

    def test_update_nonexistent_record_404(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        resp = client.put("/api/v1/attendance/9999", json={"status": "present"}, headers=auth_headers)
        assert resp.status_code == 404


class TestQueryAttendance:
    def test_teacher_sees_only_own_students(
        self, client: TestClient, auth_headers: dict[str, str], student: Student, other_teacher_student: Student
    ) -> None:
        client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-01", "present"),
            headers=auth_headers,
        )
        resp = client.get("/api/v1/attendance", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert all(item["student_id"] == student.id for item in body)

    def test_parent_sees_only_linked_child(
        self, client: TestClient, auth_headers: dict[str, str], parent_auth_headers: dict[str, str], student: Student
    ) -> None:
        client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-01", "present"),
            headers=auth_headers,
        )
        resp = client.get("/api/v1/attendance", headers=parent_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["student_id"] == student.id

    def test_date_filter(
        self, client: TestClient, auth_headers: dict[str, str], student: Student
    ) -> None:
        client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-01", "present"),
            headers=auth_headers,
        )
        client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-02", "absent"),
            headers=auth_headers,
        )
        resp = client.get("/api/v1/attendance?date=2026-07-01", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["date"] == "2026-07-01"


class TestAttendanceSummary:
    def test_summary_counts_and_percentage(
        self, client: TestClient, auth_headers: dict[str, str], student: Student
    ) -> None:
        for day, status in [
            ("2026-07-01", "present"),
            ("2026-07-02", "present"),
            ("2026-07-03", "absent"),
            ("2026-07-04", "late"),
        ]:
            client.post(
                "/api/v1/attendance",
                json=_mark_payload(student.id, day, status),
                headers=auth_headers,
            )

        resp = client.get(f"/api/v1/attendance/student/{student.id}/summary", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_days"] == 4
        assert body["present_days"] == 2
        assert body["absent_days"] == 1
        assert body["late_days"] == 1
        assert body["attendance_percentage"] == 50.0

    def test_parent_can_read_summary_of_linked_child(
        self, client: TestClient, auth_headers: dict[str, str], parent_auth_headers: dict[str, str], student: Student
    ) -> None:
        client.post(
            "/api/v1/attendance",
            json=_mark_payload(student.id, "2026-07-01", "present"),
            headers=auth_headers,
        )
        resp = client.get(f"/api/v1/attendance/student/{student.id}/summary", headers=parent_auth_headers)
        assert resp.status_code == 200

    def test_unrelated_parent_denied_summary(
        self,
        client: TestClient,
        other_teacher_auth_headers: dict[str, str],
        other_teacher_student: Student,
        parent_auth_headers: dict[str, str],
    ) -> None:
        client.post(
            "/api/v1/attendance",
            json=_mark_payload(other_teacher_student.id, "2026-07-01", "present"),
            headers=other_teacher_auth_headers,
        )
        resp = client.get(
            f"/api/v1/attendance/student/{other_teacher_student.id}/summary", headers=parent_auth_headers
        )
        assert resp.status_code == 403

    def test_summary_zero_days_zero_percentage(
        self, client: TestClient, auth_headers: dict[str, str], student: Student
    ) -> None:
        resp = client.get(f"/api/v1/attendance/student/{student.id}/summary", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_days"] == 0
        assert body["attendance_percentage"] == 0.0
