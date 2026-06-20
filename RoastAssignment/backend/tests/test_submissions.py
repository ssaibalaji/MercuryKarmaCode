"""Tests for /submissions endpoints: list scoping, detail access, sync trigger."""
from datetime import datetime, timezone

from app.models.submission import Submission, SyncStatus


def _make_submission(db, user, response_id="resp-1", assignment_name="HW1"):
    submission = Submission(
        user_id=user.id,
        student_name=user.full_name or "Student",
        student_email=user.email,
        assignment_name=assignment_name,
        github_repo_url="https://github.com/owner/repo",
        google_form_response_id=response_id,
        sync_status=SyncStatus.synced,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def test_list_submissions_student_sees_only_own(
    client, db, test_student, test_examiner, student_auth_headers
):
    own = _make_submission(db, test_student, response_id="own-1")
    _make_submission(db, test_examiner, response_id="other-1")

    response = client.get("/api/v1/submissions/", headers=student_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == own.id
    assert body[0]["user_id"] == test_student.id


def test_list_submissions_examiner_sees_all(
    client, db, test_student, test_examiner, examiner_auth_headers
):
    _make_submission(db, test_student, response_id="s-1")
    _make_submission(db, test_examiner, response_id="s-2")

    response = client.get("/api/v1/submissions/", headers=examiner_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2


def test_get_submission_not_found(client, examiner_auth_headers):
    response = client.get("/api/v1/submissions/99999", headers=examiner_auth_headers)
    assert response.status_code == 404


def test_get_submission_cross_student_forbidden(
    client, db, test_student, test_examiner, student_auth_headers
):
    other_submission = _make_submission(db, test_examiner, response_id="not-mine")

    response = client.get(
        f"/api/v1/submissions/{other_submission.id}", headers=student_auth_headers
    )
    assert response.status_code == 403


def test_get_submission_own_succeeds(client, db, test_student, student_auth_headers):
    submission = _make_submission(db, test_student, response_id="mine")

    response = client.get(
        f"/api/v1/submissions/{submission.id}", headers=student_auth_headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == submission.id


def test_sync_requires_examiner_or_coach_role(client, student_auth_headers):
    response = client.post("/api/v1/submissions/sync", headers=student_auth_headers)
    assert response.status_code == 403


def test_sync_unauthenticated_rejected(client):
    response = client.post("/api/v1/submissions/sync")
    assert response.status_code == 401


def test_sync_triggers_evaluation_for_new_submissions(
    client, db, test_examiner, examiner_auth_headers, monkeypatch
):
    """Mock google_forms_sync.sync_submissions and evaluation_service.run_evaluation_for_submission
    so the test never touches real Google Sheets/GitHub/Anthropic APIs.
    """
    created = _make_submission(db, test_examiner, response_id="synced-1")

    fake_result = {
        "created": 1,
        "skipped_duplicate": 0,
        "unmatched_email": 0,
        "created_submissions": [created],
    }

    monkeypatch.setattr(
        "app.routers.submissions.sync_submissions", lambda db: fake_result
    )

    scheduled_ids = []

    def fake_run_evaluation(submission_id):
        scheduled_ids.append(submission_id)

    monkeypatch.setattr(
        "app.routers.submissions.run_evaluation_for_submission", fake_run_evaluation
    )

    response = client.post("/api/v1/submissions/sync", headers=examiner_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "created": 1,
        "skipped_duplicate": 0,
        "unmatched_email": 0,
    }
    # BackgroundTasks run after the response is sent but still within the
    # TestClient's request lifecycle, so by the time `client.post` returns
    # the background task has already executed.
    assert scheduled_ids == [created.id]


def test_sync_as_coach_allowed(client, examiner_auth_headers, monkeypatch, test_coach, coach_auth_headers):
    fake_result = {
        "created": 0,
        "skipped_duplicate": 0,
        "unmatched_email": 0,
        "created_submissions": [],
    }
    monkeypatch.setattr(
        "app.routers.submissions.sync_submissions", lambda db: fake_result
    )
    response = client.post("/api/v1/submissions/sync", headers=coach_auth_headers)
    assert response.status_code == 200
