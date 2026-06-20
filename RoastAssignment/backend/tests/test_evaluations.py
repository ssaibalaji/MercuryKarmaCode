"""Tests for /evaluations endpoints: get, retry, role scoping."""
from datetime import datetime, timezone

from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission, SyncStatus


def _make_submission(db, user, response_id="resp-1"):
    submission = Submission(
        user_id=user.id,
        student_name=user.full_name or "Student",
        student_email=user.email,
        assignment_name="HW1",
        github_repo_url="https://github.com/owner/repo",
        google_form_response_id=response_id,
        sync_status=SyncStatus.synced,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def _make_evaluation(db, submission, status=EvaluationStatus.completed, overall_score=0.75):
    evaluation = Evaluation(
        submission_id=submission.id,
        ai_roast_text="Decent work.",
        ai_score=0.8,
        static_analysis_report={"issues": []},
        static_analysis_score=0.7,
        overall_score=overall_score,
        status=status,
        evaluated_at=datetime.now(timezone.utc),
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


def test_get_evaluation_not_found(client, examiner_auth_headers):
    response = client.get("/api/v1/evaluations/99999", headers=examiner_auth_headers)
    assert response.status_code == 404


def test_get_evaluation_cross_student_forbidden(
    client, db, test_student, test_examiner, student_auth_headers
):
    other_submission = _make_submission(db, test_examiner, response_id="other")
    _make_evaluation(db, other_submission)

    response = client.get(
        f"/api/v1/evaluations/{other_submission.id}", headers=student_auth_headers
    )
    assert response.status_code == 403


def test_get_evaluation_own_succeeds(client, db, test_student, student_auth_headers):
    submission = _make_submission(db, test_student, response_id="mine")
    evaluation = _make_evaluation(db, submission)

    response = client.get(
        f"/api/v1/evaluations/{submission.id}", headers=student_auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == evaluation.id
    assert body["status"] == "completed"


def test_get_evaluation_examiner_can_view_any(
    client, db, test_student, examiner_auth_headers
):
    submission = _make_submission(db, test_student, response_id="any")
    _make_evaluation(db, submission)

    response = client.get(
        f"/api/v1/evaluations/{submission.id}", headers=examiner_auth_headers
    )
    assert response.status_code == 200


def test_retry_requires_examiner_or_coach_role(
    client, db, test_student, student_auth_headers
):
    submission = _make_submission(db, test_student, response_id="retry-1")

    response = client.post(
        f"/api/v1/evaluations/{submission.id}/retry", headers=student_auth_headers
    )
    assert response.status_code == 403


def test_retry_unauthenticated_rejected(client, db, test_student):
    submission = _make_submission(db, test_student, response_id="retry-2")
    response = client.post(f"/api/v1/evaluations/{submission.id}/retry")
    assert response.status_code == 401


def test_retry_not_found(client, examiner_auth_headers):
    response = client.post(
        "/api/v1/evaluations/99999/retry", headers=examiner_auth_headers
    )
    assert response.status_code == 404


def test_retry_schedules_background_evaluation(
    client, db, test_student, examiner_auth_headers, monkeypatch
):
    submission = _make_submission(db, test_student, response_id="retry-3")
    _make_evaluation(db, submission, status=EvaluationStatus.failed, overall_score=None)

    scheduled_ids = []

    def fake_run_evaluation(submission_id):
        scheduled_ids.append(submission_id)

    monkeypatch.setattr(
        "app.routers.evaluations.run_evaluation_for_submission", fake_run_evaluation
    )

    response = client.post(
        f"/api/v1/evaluations/{submission.id}/retry", headers=examiner_auth_headers
    )
    assert response.status_code == 200
    assert response.json() == {"status": "retry_scheduled"}
    assert scheduled_ids == [submission.id]


def test_add_comment_requires_examiner_or_coach_role(
    client, db, test_student, student_auth_headers
):
    submission = _make_submission(db, test_student, response_id="comment-1")
    _make_evaluation(db, submission)

    response = client.put(
        f"/api/v1/evaluations/{submission.id}",
        headers=student_auth_headers,
        json={"comment": "Nice work"},
    )
    assert response.status_code == 403


def test_add_comment_not_persisted(client, db, test_student, examiner_auth_headers):
    """The PUT endpoint appends the comment to the response only (documented
    limitation: Evaluation has no `comment` column). A follow-up GET must not
    show it.
    """
    submission = _make_submission(db, test_student, response_id="comment-2")
    _make_evaluation(db, submission)

    put_response = client.put(
        f"/api/v1/evaluations/{submission.id}",
        headers=examiner_auth_headers,
        json={"comment": "Great job overall"},
    )
    assert put_response.status_code == 200
    assert "Great job overall" in put_response.json()["ai_roast_text"]

    get_response = client.get(
        f"/api/v1/evaluations/{submission.id}", headers=examiner_auth_headers
    )
    assert "Great job overall" not in (get_response.json()["ai_roast_text"] or "")
