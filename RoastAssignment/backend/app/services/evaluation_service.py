"""Orchestrates a full evaluation run for a submission.

`run_evaluation_for_submission` is the contract entry point called both by this
module's own router (retry endpoint) and by BACKEND-SUBMISSIONS's background
sync job. It opens its own DB session (via `SessionLocal`) rather than relying
on a request-scoped session, since it is designed to run as a FastAPI
`BackgroundTasks` job (i.e. outside the request lifecycle).
"""
import logging
from datetime import datetime, timezone

from app.config import settings
from app.database import SessionLocal
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission
from app.services.ai_roast import generate_roast
from app.services.github_fetcher import GitHubFetchError, fetch_repo_files
from app.services.static_analysis import run_static_analysis

logger = logging.getLogger(__name__)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


async def run_evaluation_for_submission(submission_id: int) -> None:
    """Run the full evaluation pipeline for `submission_id` and persist the result.

    Scale note: `ai_score`, `static_analysis_score`, and `overall_score` are all
    stored as floats in the 0.0-1.0 range (not 0-100). `generate_roast` already
    normalizes its parsed 0-100 SCORE line to 0.0-1.0, and `run_static_analysis`
    returns a 0.0-1.0 heuristic score natively, so `overall_score` (the weighted
    blend) stays consistent on the same 0.0-1.0 scale.

    On any failure (GitHubFetchError or unexpected exception), marks the
    evaluation status="failed", records the error message in `ai_roast_text`,
    commits, and logs the exception. This function never raises -- it runs in a
    background task with nothing to catch an exception.
    """
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission is None:
            logger.error("run_evaluation_for_submission: submission %s not found", submission_id)
            return

        evaluation = (
            db.query(Evaluation).filter(Evaluation.submission_id == submission_id).first()
        )
        if evaluation is None:
            evaluation = Evaluation(submission_id=submission_id)
            db.add(evaluation)
        elif evaluation.status == EvaluationStatus.running:
            # Another concurrent task already picked this up (e.g. scheduler + retry race).
            logger.warning(
                "Evaluation for submission %s is already running; skipping duplicate dispatch",
                submission_id,
            )
            return

        evaluation.status = EvaluationStatus.running
        db.commit()

        try:
            files = await fetch_repo_files(submission.github_repo_url)
            ai_text, ai_score = await generate_roast(files)
            report, static_score = run_static_analysis(files)

            ai_score = _clamp01(ai_score)
            static_score = _clamp01(static_score)
            overall_score = _clamp01(
                settings.EVALUATION_AI_WEIGHT * ai_score
                + settings.EVALUATION_STATIC_WEIGHT * static_score
            )

            evaluation.ai_roast_text = ai_text
            evaluation.ai_score = ai_score
            evaluation.static_analysis_report = report
            evaluation.static_analysis_score = static_score
            evaluation.overall_score = overall_score
            evaluation.status = EvaluationStatus.completed
            evaluation.evaluated_at = datetime.now(timezone.utc)
            db.commit()

            try:
                from app.services.email import send_evaluation_complete_email

                await send_evaluation_complete_email(submission)
            except Exception as exc:  # noqa: BLE001 - notifications must never break evaluation
                logger.warning(
                    "send_evaluation_complete_email unavailable or failed for submission %s: %s",
                    submission_id,
                    exc,
                )

        except GitHubFetchError as exc:
            logger.error(
                "Evaluation failed for submission %s (GitHub fetch error): %s",
                submission_id,
                exc,
            )
            evaluation.status = EvaluationStatus.failed
            evaluation.ai_roast_text = f"Evaluation failed: {exc}"
            db.commit()
        except Exception as exc:  # noqa: BLE001 - background task: nothing else catches this
            logger.exception(
                "Evaluation failed for submission %s (unexpected error): %s",
                submission_id,
                exc,
            )
            evaluation.status = EvaluationStatus.failed
            evaluation.ai_roast_text = f"Evaluation failed: {exc}"
            db.commit()

    finally:
        db.close()
