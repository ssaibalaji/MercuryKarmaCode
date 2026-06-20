"""Tests for /dashboard endpoints: role-scoped stats, examiner/coach-only analytics."""
from datetime import datetime, timezone

from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission, SyncStatus


def _make_submission(db, user, response_id, assignment_name="HW1"):
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


def _make_evaluation(db, submission, status=EvaluationStatus.completed, overall_score=0.5):
    evaluation = Evaluation(
        submission_id=submission.id,
        status=status,
        overall_score=overall_score,
        evaluated_at=datetime.now(timezone.utc) if status == EvaluationStatus.completed else None,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


def test_stats_student_sees_only_own_counts(
    client, db, test_student, test_examiner, student_auth_headers
):
    own_submission = _make_submission(db, test_student, "s-own")
    _make_evaluation(db, own_submission, status=EvaluationStatus.completed, overall_score=0.9)

    other_submission = _make_submission(db, test_examiner, "s-other")
    _make_evaluation(db, other_submission, status=EvaluationStatus.completed, overall_score=0.1)

    response = client.get("/api/v1/dashboard/stats", headers=student_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_submissions"] == 1
    assert body["completed_evaluations"] == 1
    assert body["average_overall_score"] == 0.9


def test_stats_examiner_sees_global_counts(
    client, db, test_student, test_examiner, examiner_auth_headers
):
    own_submission = _make_submission(db, test_student, "g-own")
    _make_evaluation(db, own_submission, status=EvaluationStatus.completed, overall_score=0.9)

    other_submission = _make_submission(db, test_examiner, "g-other")
    _make_evaluation(db, other_submission, status=EvaluationStatus.failed, overall_score=None)

    response = client.get("/api/v1/dashboard/stats", headers=examiner_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_submissions"] == 2
    assert body["completed_evaluations"] == 1
    assert body["failed_evaluations"] == 1


def test_stats_pending_and_running_are_combined(
    client, db, test_student, student_auth_headers
):
    pending_submission = _make_submission(db, test_student, "p-1")
    _make_evaluation(db, pending_submission, status=EvaluationStatus.pending, overall_score=None)

    running_submission = _make_submission(db, test_student, "p-2")
    _make_evaluation(db, running_submission, status=EvaluationStatus.running, overall_score=None)

    response = client.get("/api/v1/dashboard/stats", headers=student_auth_headers)
    assert response.status_code == 200
    assert response.json()["pending_evaluations"] == 2


def test_stats_unauthenticated_rejected(client):
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401


def test_score_distribution_requires_examiner_or_coach(client, student_auth_headers):
    response = client.get(
        "/api/v1/dashboard/analytics/score-distribution", headers=student_auth_headers
    )
    assert response.status_code == 403


def test_score_distribution_examiner_allowed(
    client, db, test_student, examiner_auth_headers
):
    submission = _make_submission(db, test_student, "dist-1")
    _make_evaluation(db, submission, status=EvaluationStatus.completed, overall_score=0.85)

    response = client.get(
        "/api/v1/dashboard/analytics/score-distribution", headers=examiner_auth_headers
    )
    assert response.status_code == 200
    buckets = response.json()
    assert sum(b["count"] for b in buckets) == 1
    top_bucket = next(b for b in buckets if b["range"] == "0.8-1.0")
    assert top_bucket["count"] == 1


def test_submissions_over_time_requires_examiner_or_coach(client, student_auth_headers):
    response = client.get(
        "/api/v1/dashboard/analytics/submissions-over-time",
        headers=student_auth_headers,
    )
    assert response.status_code == 403


def test_submissions_over_time_coach_allowed(
    client, db, test_student, coach_auth_headers
):
    _make_submission(db, test_student, "time-1")

    response = client.get(
        "/api/v1/dashboard/analytics/submissions-over-time",
        headers=coach_auth_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
