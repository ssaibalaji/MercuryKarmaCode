"""Tests for the fee-schedule feature: calculate_monthly_fee, student
create/update auto-calc wiring, the monthly-fee preview endpoint, and the
attendance calendar-summary endpoint.
"""
import calendar
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord
from app.models.student import Student
from app.models.user import User
from app.services.student_service import calculate_monthly_fee

STUDENTS_URL = "/api/v1/students"
ATTENDANCE_URL = "/api/v1/attendance"


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


class TestCalculateMonthlyFee:
    def test_zero_when_daily_fee_is_none(self) -> None:
        assert calculate_monthly_fee(None, ["mon"], 2026, 7) == Decimal("0.00")

    def test_zero_when_no_scheduled_days(self) -> None:
        assert calculate_monthly_fee(Decimal("100"), [], 2026, 7) == Decimal("0.00")

    def test_single_weekday_count(self) -> None:
        # July 2026: count Mondays.
        year, month = 2026, 7
        _, days_in_month = calendar.monthrange(year, month)
        mondays = sum(
            1 for day in range(1, days_in_month + 1) if date(year, month, day).weekday() == 0
        )
        result = calculate_monthly_fee(Decimal("50.00"), ["mon"], year, month)
        assert result == Decimal("50.00") * mondays

    def test_multiple_weekdays_count(self) -> None:
        year, month = 2026, 7
        _, days_in_month = calendar.monthrange(year, month)
        target = {0, 2, 4}  # mon, wed, fri
        matching = sum(
            1
            for day in range(1, days_in_month + 1)
            if date(year, month, day).weekday() in target
        )
        result = calculate_monthly_fee(Decimal("20.00"), ["mon", "wed", "fri"], year, month)
        assert result == Decimal("20.00") * matching

    def test_sunday_code_maps_to_python_weekday_six(self) -> None:
        year, month = 2026, 7
        _, days_in_month = calendar.monthrange(year, month)
        sundays = sum(
            1 for day in range(1, days_in_month + 1) if date(year, month, day).weekday() == 6
        )
        result = calculate_monthly_fee(Decimal("10.00"), ["sun"], year, month)
        assert result == Decimal("10.00") * sundays


class TestStudentAutoCalc:
    def test_create_auto_computes_monthly_fee_for_current_month(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        today = date.today()
        expected = calculate_monthly_fee(
            Decimal("40.00"), ["mon", "wed"], today.year, today.month
        )

        resp = client.post(
            STUDENTS_URL,
            json=_student_payload(daily_fee="40.00", scheduled_days=["mon", "wed"]),
            headers=auth_headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert Decimal(body["monthly_fee"]) == expected

    def test_create_explicit_monthly_fee_is_not_overwritten(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.post(
            STUDENTS_URL,
            json=_student_payload(
                daily_fee="40.00", scheduled_days=["mon", "wed"], monthly_fee="999.99"
            ),
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["monthly_fee"] == "999.99"

    def test_update_daily_fee_recomputes_monthly_fee(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        created = client.post(
            STUDENTS_URL,
            json=_student_payload(daily_fee="10.00", scheduled_days=["mon"]),
            headers=auth_headers,
        ).json()
        student_id = created["id"]

        today = date.today()
        expected = calculate_monthly_fee(Decimal("25.00"), ["mon"], today.year, today.month)

        update_resp = client.put(
            f"{STUDENTS_URL}/{student_id}",
            json={"daily_fee": "25.00"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert Decimal(update_resp.json()["monthly_fee"]) == expected

    def test_update_scheduled_days_recomputes_monthly_fee(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        created = client.post(
            STUDENTS_URL,
            json=_student_payload(daily_fee="10.00", scheduled_days=["mon"]),
            headers=auth_headers,
        ).json()
        student_id = created["id"]

        today = date.today()
        expected = calculate_monthly_fee(
            Decimal("10.00"), ["mon", "tue", "wed"], today.year, today.month
        )

        update_resp = client.put(
            f"{STUDENTS_URL}/{student_id}",
            json={"scheduled_days": ["mon", "tue", "wed"]},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert Decimal(update_resp.json()["monthly_fee"]) == expected

    def test_update_explicit_monthly_fee_overrides(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        created = client.post(
            STUDENTS_URL,
            json=_student_payload(daily_fee="10.00", scheduled_days=["mon"]),
            headers=auth_headers,
        ).json()
        student_id = created["id"]

        update_resp = client.put(
            f"{STUDENTS_URL}/{student_id}",
            json={"daily_fee": "99.00", "monthly_fee": "5.00"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["monthly_fee"] == "5.00"

    def test_invalid_scheduled_day_rejected(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.post(
            STUDENTS_URL,
            json=_student_payload(daily_fee="10.00", scheduled_days=["funday"]),
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestMonthlyFeePreviewEndpoint:
    def test_preview_returns_calculated_value_without_mutating_stored_fee(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        created = client.post(
            STUDENTS_URL,
            json=_student_payload(daily_fee="15.00", scheduled_days=["fri"]),
            headers=auth_headers,
        ).json()
        student_id = created["id"]
        stored_monthly_fee = created["monthly_fee"]

        # Preview an arbitrary future month.
        preview_resp = client.get(
            f"{STUDENTS_URL}/{student_id}/monthly-fee?year=2027&month=12",
            headers=auth_headers,
        )
        assert preview_resp.status_code == 200
        body = preview_resp.json()
        assert body["year"] == 2027
        assert body["month"] == 12
        expected = calculate_monthly_fee(Decimal("15.00"), ["fri"], 2027, 12)
        assert Decimal(body["calculated_monthly_fee"]) == expected

        # Stored value on the student record is untouched.
        get_resp = client.get(f"{STUDENTS_URL}/{student_id}", headers=auth_headers)
        assert get_resp.json()["monthly_fee"] == stored_monthly_fee

    def test_preview_defaults_to_current_month(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        created = client.post(
            STUDENTS_URL,
            json=_student_payload(daily_fee="15.00", scheduled_days=["fri"]),
            headers=auth_headers,
        ).json()
        student_id = created["id"]

        today = date.today()
        preview_resp = client.get(
            f"{STUDENTS_URL}/{student_id}/monthly-fee", headers=auth_headers
        )
        assert preview_resp.status_code == 200
        body = preview_resp.json()
        assert body["year"] == today.year
        assert body["month"] == today.month


class TestCalendarSummaryEndpoint:
    def test_returns_empty_days_when_no_attendance(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            f"{ATTENDANCE_URL}/calendar-summary?year=2026&month=7", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["days"] == []

    def test_correct_per_day_counts(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_db: Session,
        teacher_user: User,
    ) -> None:
        s1 = Student(
            teacher_id=teacher_user.id,
            full_name="Cal One",
            date_of_birth=date(2012, 1, 1),
            class_grade="5",
            enrollment_date=date(2023, 6, 1),
            is_active=True,
        )
        s2 = Student(
            teacher_id=teacher_user.id,
            full_name="Cal Two",
            date_of_birth=date(2012, 1, 1),
            class_grade="5",
            enrollment_date=date(2023, 6, 1),
            is_active=True,
        )
        test_db.add_all([s1, s2])
        test_db.commit()
        test_db.refresh(s1)
        test_db.refresh(s2)

        records = [
            AttendanceRecord(
                student_id=s1.id, teacher_id=teacher_user.id, date=date(2026, 7, 1), status="present"
            ),
            AttendanceRecord(
                student_id=s2.id, teacher_id=teacher_user.id, date=date(2026, 7, 1), status="absent"
            ),
            AttendanceRecord(
                student_id=s1.id, teacher_id=teacher_user.id, date=date(2026, 7, 2), status="late"
            ),
        ]
        test_db.add_all(records)
        test_db.commit()

        resp = client.get(
            f"{ATTENDANCE_URL}/calendar-summary?year=2026&month=7", headers=auth_headers
        )
        assert resp.status_code == 200
        days = {d["date"]: d for d in resp.json()["days"]}
        assert days["2026-07-01"] == {
            "date": "2026-07-01",
            "present": 1,
            "absent": 1,
            "late": 0,
            "total": 2,
        }
        assert days["2026-07-02"] == {
            "date": "2026-07-02",
            "present": 0,
            "absent": 0,
            "late": 1,
            "total": 1,
        }

    def test_teacher_only_sees_own_students(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        test_db: Session,
        teacher_user: User,
        other_teacher_user: User,
        other_teacher_auth_headers: dict[str, str],
    ) -> None:
        mine = Student(
            teacher_id=teacher_user.id,
            full_name="Mine",
            date_of_birth=date(2012, 1, 1),
            class_grade="5",
            enrollment_date=date(2023, 6, 1),
            is_active=True,
        )
        theirs = Student(
            teacher_id=other_teacher_user.id,
            full_name="Theirs",
            date_of_birth=date(2012, 1, 1),
            class_grade="5",
            enrollment_date=date(2023, 6, 1),
            is_active=True,
        )
        test_db.add_all([mine, theirs])
        test_db.commit()
        test_db.refresh(mine)
        test_db.refresh(theirs)

        test_db.add_all(
            [
                AttendanceRecord(
                    student_id=mine.id, teacher_id=teacher_user.id, date=date(2026, 7, 1), status="present"
                ),
                AttendanceRecord(
                    student_id=theirs.id,
                    teacher_id=other_teacher_user.id,
                    date=date(2026, 7, 1),
                    status="absent",
                ),
            ]
        )
        test_db.commit()

        resp = client.get(
            f"{ATTENDANCE_URL}/calendar-summary?year=2026&month=7", headers=auth_headers
        )
        assert resp.status_code == 200
        days = resp.json()["days"]
        assert len(days) == 1
        assert days[0]["present"] == 1
        assert days[0]["absent"] == 0
        assert days[0]["total"] == 1

    def test_parent_cannot_access_calendar_summary(
        self, client: TestClient, parent_auth_headers: dict[str, str]
    ) -> None:
        resp = client.get(
            f"{ATTENDANCE_URL}/calendar-summary?year=2026&month=7", headers=parent_auth_headers
        )
        assert resp.status_code == 403
