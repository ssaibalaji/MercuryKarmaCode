"""Tests for the Fees & Payments module.

Covers: outstanding balance calculation, overdue detection, and - critically -
that the Razorpay webhook rejects unsigned/badly-signed payloads (400, no
completed payment created) while accepting correctly-signed ones.
"""
import hashlib
import hmac
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord, AttendanceStatus
from app.models.fee import FeeFrequency, FeeStructure, Payment, PaymentMethod, PaymentStatus
from app.models.student import Student
from app.models.user import User


@pytest.fixture()
def student(test_db: Session, teacher_user: User) -> Student:
    s = Student(
        teacher_id=teacher_user.id,
        full_name="Jane Doe",
        date_of_birth=date(2012, 5, 1),
        class_grade="7",
        enrollment_date=date(2023, 6, 1),
        parent_email="parent@example.com",
    )
    test_db.add(s)
    test_db.commit()
    test_db.refresh(s)
    return s


def _make_fee(db: Session, student: Student, *, amount: str, due_date: date) -> FeeStructure:
    fee = FeeStructure(
        student_id=student.id,
        amount=Decimal(amount),
        frequency=FeeFrequency.monthly,
        due_date=due_date,
    )
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return fee


def _make_payment(
    db: Session, fee: FeeStructure, student: Student, *, amount: str, status: PaymentStatus, order_id: str | None = None
) -> Payment:
    payment = Payment(
        fee_structure_id=fee.id,
        student_id=student.id,
        amount_paid=Decimal(amount),
        payment_date=datetime.now(timezone.utc),
        method=PaymentMethod.razorpay,
        razorpay_order_id=order_id,
        status=status,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


# --- Outstanding balance -----------------------------------------------------


def test_outstanding_balance_excludes_pending_and_failed_payments(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="1000.00", due_date=date.today() + timedelta(days=10))
    _make_payment(test_db, fee, student, amount="300.00", status=PaymentStatus.completed)
    _make_payment(test_db, fee, student, amount="200.00", status=PaymentStatus.pending)
    _make_payment(test_db, fee, student, amount="500.00", status=PaymentStatus.failed)

    response = client.get(f"/api/v1/fees/students/{student.id}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_outstanding"] == "700.00"
    assert body["fee_structures"][0]["outstanding_balance"] == "700.00"
    assert body["fee_structures"][0]["is_overdue"] is False


def test_fully_paid_fee_has_zero_balance_and_is_not_overdue(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() - timedelta(days=5))
    _make_payment(test_db, fee, student, amount="500.00", status=PaymentStatus.completed)

    response = client.get(f"/api/v1/fees/students/{student.id}", headers=auth_headers)

    assert response.status_code == 200
    fee_data = response.json()["fee_structures"][0]
    assert fee_data["outstanding_balance"] == "0.00"
    assert fee_data["is_overdue"] is False


# --- Overdue detection --------------------------------------------------------


def test_overdue_endpoint_returns_only_past_due_unpaid_fees(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    overdue_fee = _make_fee(test_db, student, amount="400.00", due_date=date.today() - timedelta(days=3))
    _make_fee(test_db, student, amount="400.00", due_date=date.today() + timedelta(days=3))
    paid_overdue_fee = _make_fee(test_db, student, amount="400.00", due_date=date.today() - timedelta(days=1))
    _make_payment(test_db, paid_overdue_fee, student, amount="400.00", status=PaymentStatus.completed)

    response = client.get("/api/v1/fees/overdue", headers=auth_headers)

    assert response.status_code == 200
    ids = [f["id"] for f in response.json()]
    assert ids == [overdue_fee.id]


def test_overdue_scoped_to_teachers_own_students(
    client: TestClient,
    test_db: Session,
    student: Student,
    other_teacher_auth_headers: dict[str, str],
) -> None:
    _make_fee(test_db, student, amount="400.00", due_date=date.today() - timedelta(days=3))

    response = client.get("/api/v1/fees/overdue", headers=other_teacher_auth_headers)

    assert response.status_code == 200
    assert response.json() == []


# --- Razorpay webhook signature verification (critical security rule) -------


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_webhook_rejects_unsigned_payload(
    client: TestClient, test_db: Session, student: Student
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=5))
    payment = _make_payment(
        test_db, fee, student, amount="500.00", status=PaymentStatus.pending, order_id="order_abc123"
    )

    body = json.dumps(
        {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"id": "pay_xyz", "order_id": "order_abc123", "status": "captured"}}},
        }
    ).encode("utf-8")

    response = client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    test_db.refresh(payment)
    assert payment.status == PaymentStatus.pending


def test_webhook_rejects_badly_signed_payload(
    client: TestClient, test_db: Session, student: Student
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=5))
    payment = _make_payment(
        test_db, fee, student, amount="500.00", status=PaymentStatus.pending, order_id="order_abc123"
    )

    body = json.dumps(
        {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"id": "pay_xyz", "order_id": "order_abc123", "status": "captured"}}},
        }
    ).encode("utf-8")

    response = client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": "not-a-valid-signature"},
    )

    assert response.status_code == 400
    test_db.refresh(payment)
    assert payment.status == PaymentStatus.pending


def test_webhook_accepts_correctly_signed_payload_and_completes_payment(
    client: TestClient, test_db: Session, student: Student, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")

    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=5))
    payment = _make_payment(
        test_db, fee, student, amount="500.00", status=PaymentStatus.pending, order_id="order_abc123"
    )

    body = json.dumps(
        {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"id": "pay_xyz", "order_id": "order_abc123", "status": "captured"}}},
        }
    ).encode("utf-8")
    signature = _sign("test_webhook_secret", body)

    response = client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature},
    )

    assert response.status_code == 200
    test_db.refresh(payment)
    assert payment.status == PaymentStatus.completed
    assert payment.razorpay_payment_id == "pay_xyz"


def test_webhook_marks_payment_failed_on_payment_failed_event(
    client: TestClient, test_db: Session, student: Student, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")

    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=5))
    payment = _make_payment(
        test_db, fee, student, amount="500.00", status=PaymentStatus.pending, order_id="order_def456"
    )

    body = json.dumps(
        {
            "event": "payment.failed",
            "payload": {"payment": {"entity": {"id": "pay_failed", "order_id": "order_def456", "status": "failed"}}},
        }
    ).encode("utf-8")
    signature = _sign("test_webhook_secret", body)

    response = client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature},
    )

    assert response.status_code == 200
    test_db.refresh(payment)
    assert payment.status == PaymentStatus.failed


# --- Helpers for the new tests below ------------------------------------------


def _make_student(
    db: Session,
    teacher: User,
    *,
    parent_email: str | None = "parent@example.com",
    parent_user_id: int | None = None,
    daily_fee: Decimal | None = None,
    scheduled_days: list[str] | None = None,
    monthly_fee: Decimal | None = None,
) -> Student:
    s = Student(
        teacher_id=teacher.id,
        full_name="Extra Student",
        date_of_birth=date(2011, 3, 15),
        class_grade="6",
        enrollment_date=date(2023, 6, 1),
        parent_email=parent_email,
        parent_user_id=parent_user_id,
        daily_fee=daily_fee,
        scheduled_days=scheduled_days or [],
        monthly_fee=monthly_fee,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# --- create_fee_structure -----------------------------------------------------


def test_create_fee_structure_forbidden_for_non_owning_teacher(
    client: TestClient, test_db: Session, student: Student, other_teacher_auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/fees",
        headers=other_teacher_auth_headers,
        json={
            "student_id": student.id,
            "amount": "500.00",
            "frequency": "monthly",
            "due_date": str(date.today() + timedelta(days=10)),
        },
    )
    assert response.status_code == 403


def test_create_fee_structure_not_found_for_unknown_student(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/fees",
        headers=auth_headers,
        json={
            "student_id": 999999,
            "amount": "500.00",
            "frequency": "monthly",
            "due_date": str(date.today() + timedelta(days=10)),
        },
    )
    assert response.status_code == 404


# --- update_fee_structure ------------------------------------------------------


def test_update_fee_structure_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.put(
        "/api/v1/fees/999999",
        headers=auth_headers,
        json={"amount": "600.00"},
    )
    assert response.status_code == 404


def test_update_fee_structure_forbidden_for_non_owning_teacher(
    client: TestClient, test_db: Session, student: Student, other_teacher_auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=10))

    response = client.put(
        f"/api/v1/fees/{fee.id}",
        headers=other_teacher_auth_headers,
        json={"amount": "600.00"},
    )
    assert response.status_code == 403


def test_update_fee_structure_applies_partial_update(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=10))

    response = client.put(
        f"/api/v1/fees/{fee.id}",
        headers=auth_headers,
        json={"amount": "750.00"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == "750.00"
    # Untouched fields are unaffected by the partial update.
    assert body["frequency"] == "monthly"


# --- send_reminder --------------------------------------------------------------


def test_send_reminder_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/api/v1/fees/999999/remind", headers=auth_headers)
    assert response.status_code == 404


def test_send_reminder_forbidden_for_non_owning_teacher(
    client: TestClient, test_db: Session, student: Student, other_teacher_auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() - timedelta(days=3))

    response = client.post(f"/api/v1/fees/{fee.id}/remind", headers=other_teacher_auth_headers)
    assert response.status_code == 403


def test_send_reminder_conflict_when_not_overdue(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=10))

    response = client.post(f"/api/v1/fees/{fee.id}/remind", headers=auth_headers)
    assert response.status_code == 409


def test_send_reminder_conflict_when_no_parent_email(
    client: TestClient, test_db: Session, teacher_user: User, auth_headers: dict[str, str]
) -> None:
    student_no_email = _make_student(test_db, teacher_user, parent_email=None)
    fee = _make_fee(test_db, student_no_email, amount="500.00", due_date=date.today() - timedelta(days=3))

    response = client.post(f"/api/v1/fees/{fee.id}/remind", headers=auth_headers)
    assert response.status_code == 409


def test_send_reminder_success_creates_sent_reminder_and_calls_email_service(
    client: TestClient,
    test_db: Session,
    student: Student,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() - timedelta(days=3))

    sent_calls: list[dict[str, Any]] = []

    def _fake_send_email(to: str, subject: str, body: str) -> bool:
        sent_calls.append({"to": to, "subject": subject, "body": body})
        return True

    monkeypatch.setattr("app.services.fee_service.email_service.send_email", _fake_send_email)

    response = client.post(f"/api/v1/fees/{fee.id}/remind", headers=auth_headers)

    assert response.status_code == 202
    assert len(sent_calls) == 1
    assert sent_calls[0]["to"] == student.parent_email
    assert student.full_name in sent_calls[0]["subject"]

    from app.models.fee import FeeReminder, ReminderStatus

    reminder = test_db.query(FeeReminder).filter(FeeReminder.fee_structure_id == fee.id).first()
    assert reminder is not None
    assert reminder.status == ReminderStatus.sent


# --- create_payment_order -------------------------------------------------------


def test_create_payment_order_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/payments/razorpay/order", headers=auth_headers, json={"fee_structure_id": 999999}
    )
    assert response.status_code == 404


def test_create_payment_order_forbidden_for_unrelated_teacher(
    client: TestClient, test_db: Session, student: Student, other_teacher_auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=10))

    response = client.post(
        "/api/v1/payments/razorpay/order",
        headers=other_teacher_auth_headers,
        json={"fee_structure_id": fee.id},
    )
    assert response.status_code == 403


def test_create_payment_order_conflict_when_no_outstanding_balance(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=10))
    _make_payment(test_db, fee, student, amount="500.00", status=PaymentStatus.completed)

    response = client.post(
        "/api/v1/payments/razorpay/order", headers=auth_headers, json={"fee_structure_id": fee.id}
    )
    assert response.status_code == 409


def test_create_payment_order_success_creates_pending_payment(
    client: TestClient,
    test_db: Session,
    student: Student,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=10))

    def _fake_create_order(amount: Decimal, student_id: int) -> dict[str, Any]:
        assert amount == Decimal("500.00")
        assert student_id == student.id
        return {"id": "order_fake123", "amount": 50000, "currency": "INR"}

    monkeypatch.setattr("app.services.fee_service.razorpay_service.create_order", _fake_create_order)

    response = client.post(
        "/api/v1/payments/razorpay/order", headers=auth_headers, json={"fee_structure_id": fee.id}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["order_id"] == "order_fake123"
    assert body["amount"] == 50000

    payment = test_db.query(Payment).filter(Payment.razorpay_order_id == "order_fake123").first()
    assert payment is not None
    assert payment.status == PaymentStatus.pending
    assert payment.amount_paid == Decimal("500.00")


# --- get_payment_history ---------------------------------------------------------


def test_get_payment_history_scoped_to_linked_parent(
    client: TestClient, test_db: Session, teacher_user: User, parent_user: User, parent_auth_headers: dict[str, str]
) -> None:
    linked_student = _make_student(test_db, teacher_user, parent_user_id=parent_user.id)
    fee = _make_fee(test_db, linked_student, amount="500.00", due_date=date.today() + timedelta(days=5))
    _make_payment(test_db, fee, linked_student, amount="200.00", status=PaymentStatus.completed)

    response = client.get(f"/api/v1/payments/student/{linked_student.id}", headers=parent_auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_payment_history_forbidden_for_unlinked_parent(
    client: TestClient, test_db: Session, student: Student, parent_auth_headers: dict[str, str]
) -> None:
    # `student` fixture has no parent_user_id linked to `parent_user`.
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=5))
    _make_payment(test_db, fee, student, amount="200.00", status=PaymentStatus.completed)

    response = client.get(f"/api/v1/payments/student/{student.id}", headers=parent_auth_headers)
    assert response.status_code == 403


def test_get_payment_history_forbidden_for_cross_tenant_teacher(
    client: TestClient, test_db: Session, student: Student, other_teacher_auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=5))
    _make_payment(test_db, fee, student, amount="200.00", status=PaymentStatus.completed)

    response = client.get(f"/api/v1/payments/student/{student.id}", headers=other_teacher_auth_headers)
    assert response.status_code == 403


def test_get_payment_history_not_found_for_unknown_student(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/payments/student/999999", headers=auth_headers)
    assert response.status_code == 404


# --- record_payment_from_webhook edge cases -------------------------------------


def test_webhook_missing_order_id_returns_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")

    body = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_xyz"}}}}).encode(
        "utf-8"
    )
    signature = _sign("test_webhook_secret", body)

    response = client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature},
    )
    assert response.status_code == 404


def test_webhook_unknown_order_id_returns_404(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")

    body = json.dumps(
        {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"id": "pay_xyz", "order_id": "order_does_not_exist"}}},
        }
    ).encode("utf-8")
    signature = _sign("test_webhook_secret", body)

    response = client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature},
    )
    assert response.status_code == 404


def test_webhook_already_settled_payment_is_idempotent_noop(
    client: TestClient, test_db: Session, student: Student, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")

    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=5))
    payment = _make_payment(
        test_db,
        fee,
        student,
        amount="500.00",
        status=PaymentStatus.completed,
        order_id="order_already_done",
    )
    payment.razorpay_payment_id = "pay_original"
    test_db.commit()

    body = json.dumps(
        {
            "event": "payment.captured",
            "payload": {
                "payment": {"entity": {"id": "pay_replayed", "order_id": "order_already_done"}}
            },
        }
    ).encode("utf-8")
    signature = _sign("test_webhook_secret", body)

    response = client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature},
    )

    assert response.status_code == 200
    test_db.refresh(payment)
    # Idempotent: the already-settled payment's payment_id is unchanged, not overwritten.
    assert payment.razorpay_payment_id == "pay_original"
    assert payment.status == PaymentStatus.completed


def test_webhook_unhandled_event_type_is_noop(
    client: TestClient, test_db: Session, student: Student, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret")

    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() + timedelta(days=5))
    payment = _make_payment(
        test_db, fee, student, amount="500.00", status=PaymentStatus.pending, order_id="order_unhandled"
    )

    body = json.dumps(
        {
            "event": "payment.authorized",
            "payload": {"payment": {"entity": {"id": "pay_auth", "order_id": "order_unhandled"}}},
        }
    ).encode("utf-8")
    signature = _sign("test_webhook_secret", body)

    response = client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature},
    )

    assert response.status_code == 200
    test_db.refresh(payment)
    assert payment.status == PaymentStatus.pending


# --- generate_fees_from_attendance ---------------------------------------------

GENERATE_URL = "/api/v1/fees/generate-from-attendance"


def _past_year_month() -> tuple[int, int]:
    """A (year, month) strictly before the current calendar month."""
    today = date.today()
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def _current_year_month() -> tuple[int, int]:
    today = date.today()
    return today.year, today.month


def _mark_attendance(
    db: Session, student: Student, teacher: User, *, year: int, month: int, day: int, status: AttendanceStatus
) -> AttendanceRecord:
    record = AttendanceRecord(
        student_id=student.id,
        teacher_id=teacher.id,
        date=date(year, month, day),
        status=status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_generate_fees_creates_full_month_amount_regardless_of_attendance_mix(
    client: TestClient, test_db: Session, teacher_user: User, auth_headers: dict[str, str]
) -> None:
    year, month = _past_year_month()
    expected_amount = Decimal("2200.00")
    student = _make_student(test_db, teacher_user, monthly_fee=expected_amount)

    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=1, status=AttendanceStatus.present)
    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=2, status=AttendanceStatus.late)
    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=3, status=AttendanceStatus.absent)

    response = client.post(GENERATE_URL, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["created"]) == 1
    entry = body["created"][0]
    assert entry["student_id"] == student.id
    assert entry["year"] == year
    assert entry["month"] == month
    assert Decimal(entry["amount"]) == expected_amount

    fee = (
        test_db.query(FeeStructure)
        .filter(FeeStructure.student_id == student.id, FeeStructure.is_auto_generated.is_(True))
        .first()
    )
    assert fee is not None
    assert fee.amount == expected_amount
    assert fee.billing_year == year
    assert fee.billing_month == month


def test_generate_fees_bills_full_month_even_when_marked_absent_every_day(
    client: TestClient, test_db: Session, teacher_user: User, auth_headers: dict[str, str]
) -> None:
    """Core behavior change: attendance status no longer affects the billed amount."""
    year, month = _past_year_month()
    expected_amount = Decimal("1100.00")
    student = _make_student(test_db, teacher_user, monthly_fee=expected_amount)

    # Only one attendance record exists that month, purely as the "was active" signal,
    # and it is marked absent - the full scheduled amount must still be billed.
    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=1, status=AttendanceStatus.absent)

    response = client.post(GENERATE_URL, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["created"]) == 1
    assert Decimal(body["created"][0]["amount"]) == expected_amount
    assert expected_amount > 0

    fee = (
        test_db.query(FeeStructure)
        .filter(FeeStructure.student_id == student.id, FeeStructure.is_auto_generated.is_(True))
        .first()
    )
    assert fee is not None
    assert fee.amount == expected_amount


def test_generate_fees_skips_student_with_no_monthly_fee(
    client: TestClient, test_db: Session, teacher_user: User, auth_headers: dict[str, str]
) -> None:
    year, month = _past_year_month()
    student = _make_student(test_db, teacher_user)
    assert student.monthly_fee is None

    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=1, status=AttendanceStatus.present)

    response = client.post(GENERATE_URL, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == []
    assert body["skipped_no_daily_fee"] == 1

    assert test_db.query(FeeStructure).filter(FeeStructure.student_id == student.id).count() == 0


def test_generate_fees_skips_when_monthly_fee_is_zero(
    client: TestClient, test_db: Session, teacher_user: User, auth_headers: dict[str, str]
) -> None:
    year, month = _past_year_month()
    student = _make_student(test_db, teacher_user, monthly_fee=Decimal("0.00"))

    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=1, status=AttendanceStatus.absent)
    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=2, status=AttendanceStatus.absent)

    response = client.post(GENERATE_URL, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == []
    assert body["skipped_zero_days"] == 1

    assert test_db.query(FeeStructure).filter(FeeStructure.student_id == student.id).count() == 0


def test_generate_fees_regenerates_unpaid_fee_when_called_again(
    client: TestClient, test_db: Session, teacher_user: User, auth_headers: dict[str, str]
) -> None:
    """An already-generated but unpaid fee is recalculated (not duplicated) on re-run."""
    year, month = _past_year_month()
    student = _make_student(test_db, teacher_user, monthly_fee=Decimal("2200.00"))

    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=1, status=AttendanceStatus.present)

    first = client.post(GENERATE_URL, headers=auth_headers)
    assert first.status_code == 200
    assert len(first.json()["created"]) == 1

    # Teacher revises the student's monthly fee before the fee is ever paid.
    student.monthly_fee = Decimal("2500.00")
    test_db.commit()

    second = client.post(GENERATE_URL, headers=auth_headers)
    assert second.status_code == 200
    body = second.json()
    assert body["created"] == []
    assert len(body["updated"]) == 1
    assert Decimal(body["updated"][0]["amount"]) == Decimal("2500.00")
    assert body["skipped_already_generated"] == 0

    fees = test_db.query(FeeStructure).filter(FeeStructure.student_id == student.id).all()
    assert len(fees) == 1
    assert fees[0].amount == Decimal("2500.00")


def test_generate_fees_locks_fee_once_fully_paid(
    client: TestClient, test_db: Session, teacher_user: User, auth_headers: dict[str, str]
) -> None:
    """A fully-paid auto-generated fee is never recalculated or duplicated."""
    year, month = _past_year_month()
    student = _make_student(test_db, teacher_user, monthly_fee=Decimal("2200.00"))

    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=1, status=AttendanceStatus.present)

    first = client.post(GENERATE_URL, headers=auth_headers)
    assert first.status_code == 200
    assert len(first.json()["created"]) == 1

    fee = test_db.query(FeeStructure).filter(FeeStructure.student_id == student.id).first()
    assert fee is not None
    _make_payment(test_db, fee, student, amount="2200.00", status=PaymentStatus.completed)

    # Even if the student's monthly fee changes afterward, a paid fee must never change.
    student.monthly_fee = Decimal("9999.00")
    test_db.commit()

    second = client.post(GENERATE_URL, headers=auth_headers)
    assert second.status_code == 200
    body = second.json()
    assert body["created"] == []
    assert body["updated"] == []
    assert body["skipped_already_generated"] == 1

    fees = test_db.query(FeeStructure).filter(FeeStructure.student_id == student.id).all()
    assert len(fees) == 1
    assert fees[0].amount == Decimal("2200.00")


def test_generate_fees_never_generates_for_current_month(
    client: TestClient, test_db: Session, teacher_user: User, auth_headers: dict[str, str]
) -> None:
    year, month = _current_year_month()
    student = _make_student(test_db, teacher_user, monthly_fee=Decimal("2200.00"))

    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=1, status=AttendanceStatus.present)

    response = client.post(GENERATE_URL, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == []
    assert test_db.query(FeeStructure).filter(FeeStructure.student_id == student.id).count() == 0


def test_generate_fees_scoped_to_teachers_own_students(
    client: TestClient,
    test_db: Session,
    teacher_user: User,
    other_teacher_user: User,
    other_teacher_auth_headers: dict[str, str],
) -> None:
    year, month = _past_year_month()
    student = _make_student(test_db, teacher_user, monthly_fee=Decimal("2200.00"))

    _mark_attendance(test_db, student, teacher_user, year=year, month=month, day=1, status=AttendanceStatus.present)

    response = client.post(GENERATE_URL, headers=other_teacher_auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["created"] == []
    assert test_db.query(FeeStructure).filter(FeeStructure.student_id == student.id).count() == 0


def test_generate_fees_forbidden_for_parent(
    client: TestClient, parent_auth_headers: dict[str, str]
) -> None:
    response = client.post(GENERATE_URL, headers=parent_auth_headers)
    assert response.status_code == 403


# --- student_name on FeeStructureWithBalance ------------------------------------


def test_overdue_fees_include_student_name(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    _make_fee(test_db, student, amount="400.00", due_date=date.today() - timedelta(days=3))

    response = client.get("/api/v1/fees/overdue", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["student_name"] == student.full_name


def test_student_fee_detail_includes_student_name(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    _make_fee(test_db, student, amount="400.00", due_date=date.today() + timedelta(days=3))

    response = client.get(f"/api/v1/fees/students/{student.id}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["fee_structures"][0]["student_name"] == student.full_name


# --- mark_fee_paid ---------------------------------------------------------------

MARK_PAID_URL = "/api/v1/fees/{fee_id}/mark-paid"


def test_mark_fee_paid_zeroes_balance_and_creates_cash_payment(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() - timedelta(days=3))

    response = client.post(MARK_PAID_URL.format(fee_id=fee.id), headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["outstanding_balance"] == "0.00"
    assert body["is_overdue"] is False
    assert body["student_name"] == student.full_name

    payment = test_db.query(Payment).filter(Payment.fee_structure_id == fee.id).first()
    assert payment is not None
    assert payment.method == PaymentMethod.cash
    assert payment.status == PaymentStatus.completed
    assert payment.amount_paid == Decimal("500.00")


def test_mark_fee_paid_conflict_when_already_fully_paid(
    client: TestClient, test_db: Session, student: Student, auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() - timedelta(days=3))
    _make_payment(test_db, fee, student, amount="500.00", status=PaymentStatus.completed)

    response = client.post(MARK_PAID_URL.format(fee_id=fee.id), headers=auth_headers)

    assert response.status_code == 409


def test_mark_fee_paid_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(MARK_PAID_URL.format(fee_id=999999), headers=auth_headers)
    assert response.status_code == 404


def test_mark_fee_paid_forbidden_for_non_owning_teacher(
    client: TestClient, test_db: Session, student: Student, other_teacher_auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() - timedelta(days=3))

    response = client.post(MARK_PAID_URL.format(fee_id=fee.id), headers=other_teacher_auth_headers)
    assert response.status_code == 403


def test_mark_fee_paid_forbidden_for_parent(
    client: TestClient, test_db: Session, student: Student, parent_auth_headers: dict[str, str]
) -> None:
    fee = _make_fee(test_db, student, amount="500.00", due_date=date.today() - timedelta(days=3))

    response = client.post(MARK_PAID_URL.format(fee_id=fee.id), headers=parent_auth_headers)
    assert response.status_code == 403
