"""Tests for the teacher dashboard stats endpoint."""
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.fee import FeeStructure, FeeFrequency, Payment, PaymentMethod, PaymentStatus
from app.models.student import Student
from app.models.user import User


def _make_student(db: Session, teacher: User, *, name: str = "Student A") -> Student:
    student = Student(
        teacher_id=teacher.id,
        full_name=name,
        date_of_birth=date(2015, 1, 1),
        class_grade="5",
        enrollment_date=date(2023, 1, 1),
        is_active=True,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def test_dashboard_stats_happy_path(
    client: TestClient, test_db: Session, teacher_user: User, auth_headers: dict[str, str]
) -> None:
    student = _make_student(test_db, teacher_user)
    today = datetime.now(timezone.utc).date()

    test_db.add(AttendanceRecord(student_id=student.id, teacher_id=teacher_user.id, date=today, status=AttendanceStatus.present))
    test_db.commit()

    fee = FeeStructure(
        student_id=student.id,
        amount=1000,
        frequency=FeeFrequency.monthly,
        due_date=today - timedelta(days=5),
    )
    test_db.add(fee)
    test_db.commit()
    test_db.refresh(fee)

    payment = Payment(
        fee_structure_id=fee.id,
        student_id=student.id,
        amount_paid=1000,
        payment_date=datetime.now(timezone.utc),
        method=PaymentMethod.cash,
        status=PaymentStatus.completed,
    )
    test_db.add(payment)
    test_db.commit()

    response = client.get("/api/v1/dashboard/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == 1
    assert data["attendance_percentage_recent"] == 100.0
    assert data["overdue_fees_count"] == 0
    assert data["total_fees_collected_this_month"] == 1000.0
    assert len(data["recent_activity"]) == 2


def test_dashboard_stats_scoped_to_own_students(
    client: TestClient,
    test_db: Session,
    teacher_user: User,
    other_teacher_user: User,
    auth_headers: dict[str, str],
) -> None:
    """A teacher's dashboard must never reflect another teacher's students."""
    _make_student(test_db, other_teacher_user, name="Not Mine")

    response = client.get("/api/v1/dashboard/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == 0


def test_dashboard_stats_requires_teacher_role(
    client: TestClient, parent_auth_headers: dict[str, str]
) -> None:
    """Non-teacher roles (e.g. parent) are blocked from the teacher dashboard endpoint."""
    response = client.get("/api/v1/dashboard/stats", headers=parent_auth_headers)

    assert response.status_code == 403


def test_dashboard_stats_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard/stats")

    assert response.status_code == 401
