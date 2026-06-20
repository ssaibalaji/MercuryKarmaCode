"""Unit tests for app.services.evaluation_service.run_evaluation_for_submission.

These tests mock the three pipeline steps (fetch_repo_files, generate_roast,
run_static_analysis) so no real GitHub/Anthropic network calls happen, and
assert the scoring math (overall_score = AI_WEIGHT*ai_score + STATIC_WEIGHT*
static_score, per app/config.py's EVALUATION_AI_WEIGHT/EVALUATION_STATIC_WEIGHT,
default 0.6/0.4) and status transitions (pending -> running -> completed, or
-> failed on error).
"""
from datetime import datetime, timezone

import pytest

from app.config import settings
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission, SyncStatus
from app.services import evaluation_service
from app.services.github_fetcher import GitHubFetchError


def _make_submission(db, user, response_id="resp-svc-1"):
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


@pytest.mark.asyncio
async def test_run_evaluation_computes_weighted_score_and_completes(
    db, test_student, monkeypatch
):
    submission = _make_submission(db, test_student, response_id="svc-success")

    fake_files = [{"path": "main.py", "content": "print('hi')", "size": 12}]

    async def fake_fetch_repo_files(url):
        return fake_files

    async def fake_generate_roast(files):
        assert files == fake_files
        return "Great job, mostly.", 0.8

    def fake_run_static_analysis(files):
        assert files == fake_files
        return {"issue_count": 0}, 0.5

    async def fake_send_email(submission_obj):
        return None

    monkeypatch.setattr(
        evaluation_service, "fetch_repo_files", fake_fetch_repo_files
    )
    monkeypatch.setattr(evaluation_service, "generate_roast", fake_generate_roast)
    monkeypatch.setattr(
        evaluation_service, "run_static_analysis", fake_run_static_analysis
    )
    monkeypatch.setattr(
        "app.services.email.send_evaluation_complete_email", fake_send_email
    )

    await evaluation_service.run_evaluation_for_submission(submission.id)

    evaluation = (
        db.query(Evaluation)
        .filter(Evaluation.submission_id == submission.id)
        .first()
    )
    assert evaluation is not None
    assert evaluation.status == EvaluationStatus.completed
    assert evaluation.ai_score == 0.8
    assert evaluation.static_analysis_score == 0.5

    expected_overall = (
        settings.EVALUATION_AI_WEIGHT * 0.8 + settings.EVALUATION_STATIC_WEIGHT * 0.5
    )
    assert evaluation.overall_score == pytest.approx(expected_overall)
    assert evaluation.evaluated_at is not None
    assert evaluation.ai_roast_text == "Great job, mostly."
    assert evaluation.static_analysis_report == {"issue_count": 0}


@pytest.mark.asyncio
async def test_run_evaluation_clamps_out_of_range_scores(
    db, test_student, monkeypatch
):
    """ai_score/static_score from mocked steps are out of [0,1]; the pipeline
    must clamp both inputs and the final overall_score into [0.0, 1.0].
    """
    submission = _make_submission(db, test_student, response_id="svc-clamp")

    async def fake_fetch_repo_files(url):
        return [{"path": "a.py", "content": "x", "size": 1}]

    async def fake_generate_roast(files):
        return "roast", 1.5  # out of range, should clamp to 1.0

    def fake_run_static_analysis(files):
        return {}, -0.3  # out of range, should clamp to 0.0

    async def fake_send_email(submission_obj):
        return None

    monkeypatch.setattr(
        evaluation_service, "fetch_repo_files", fake_fetch_repo_files
    )
    monkeypatch.setattr(evaluation_service, "generate_roast", fake_generate_roast)
    monkeypatch.setattr(
        evaluation_service, "run_static_analysis", fake_run_static_analysis
    )
    monkeypatch.setattr(
        "app.services.email.send_evaluation_complete_email", fake_send_email
    )

    await evaluation_service.run_evaluation_for_submission(submission.id)

    evaluation = (
        db.query(Evaluation)
        .filter(Evaluation.submission_id == submission.id)
        .first()
    )
    assert evaluation.ai_score == 1.0
    assert evaluation.static_analysis_score == 0.0
    expected_overall = settings.EVALUATION_AI_WEIGHT * 1.0 + settings.EVALUATION_STATIC_WEIGHT * 0.0
    assert evaluation.overall_score == pytest.approx(expected_overall)
    assert evaluation.status == EvaluationStatus.completed


@pytest.mark.asyncio
async def test_run_evaluation_github_fetch_error_marks_failed(
    db, test_student, monkeypatch
):
    submission = _make_submission(db, test_student, response_id="svc-fail")

    async def fake_fetch_repo_files(url):
        raise GitHubFetchError("Repository 'owner/repo' not found or private.")

    monkeypatch.setattr(
        evaluation_service, "fetch_repo_files", fake_fetch_repo_files
    )

    await evaluation_service.run_evaluation_for_submission(submission.id)

    evaluation = (
        db.query(Evaluation)
        .filter(Evaluation.submission_id == submission.id)
        .first()
    )
    assert evaluation is not None
    assert evaluation.status == EvaluationStatus.failed
    assert "not found or private" in evaluation.ai_roast_text
    assert evaluation.overall_score is None


@pytest.mark.asyncio
async def test_run_evaluation_unexpected_error_marks_failed(
    db, test_student, monkeypatch
):
    submission = _make_submission(db, test_student, response_id="svc-fail-2")

    async def fake_fetch_repo_files(url):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        evaluation_service, "fetch_repo_files", fake_fetch_repo_files
    )

    await evaluation_service.run_evaluation_for_submission(submission.id)

    evaluation = (
        db.query(Evaluation)
        .filter(Evaluation.submission_id == submission.id)
        .first()
    )
    assert evaluation.status == EvaluationStatus.failed
    assert "boom" in evaluation.ai_roast_text


@pytest.mark.asyncio
async def test_run_evaluation_missing_submission_is_noop(db):
    """If the submission doesn't exist, the function logs and returns without
    raising or creating an Evaluation row.
    """
    await evaluation_service.run_evaluation_for_submission(999999)

    count = db.query(Evaluation).count()
    assert count == 0


@pytest.mark.asyncio
async def test_run_evaluation_reuses_existing_evaluation_row(
    db, test_student, monkeypatch
):
    """If an Evaluation row already exists for the submission (e.g. a retry),
    the pipeline updates it in place instead of creating a second row.
    """
    submission = _make_submission(db, test_student, response_id="svc-retry")
    existing = Evaluation(submission_id=submission.id, status=EvaluationStatus.failed)
    db.add(existing)
    db.commit()
    db.refresh(existing)

    async def fake_fetch_repo_files(url):
        return [{"path": "a.py", "content": "x", "size": 1}]

    async def fake_generate_roast(files):
        return "ok", 0.6

    def fake_run_static_analysis(files):
        return {}, 0.6

    async def fake_send_email(submission_obj):
        return None

    monkeypatch.setattr(
        evaluation_service, "fetch_repo_files", fake_fetch_repo_files
    )
    monkeypatch.setattr(evaluation_service, "generate_roast", fake_generate_roast)
    monkeypatch.setattr(
        evaluation_service, "run_static_analysis", fake_run_static_analysis
    )
    monkeypatch.setattr(
        "app.services.email.send_evaluation_complete_email", fake_send_email
    )

    await evaluation_service.run_evaluation_for_submission(submission.id)

    rows = db.query(Evaluation).filter(Evaluation.submission_id == submission.id).all()
    assert len(rows) == 1
    assert rows[0].id == existing.id
    assert rows[0].status == EvaluationStatus.completed
