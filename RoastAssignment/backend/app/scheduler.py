"""APScheduler registration for periodic Google Forms submission sync.

NOTE for orchestrator: this module is intentionally NOT wired into
`app/main.py`. main.py needs a startup event calling `start_scheduler()` and a
shutdown event calling `stop_scheduler()`, e.g.:

    from app.scheduler import start_scheduler, stop_scheduler

    @app.on_event("startup")
    def _on_startup():
        start_scheduler()

    @app.on_event("shutdown")
    def _on_shutdown():
        stop_scheduler()
"""
import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.database import SessionLocal
from app.services.evaluation_service import run_evaluation_for_submission
from app.services.google_forms_sync import sync_submissions

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None

JOB_ID = "google_forms_sync"


def _run_sync_job() -> None:
    """Sync job body: opens its own DB session, syncs, then dispatches evaluation.

    Runs in APScheduler's background thread, so it owns its own `Session`
    (request-scoped sessions from `get_db` are not available here) and runs the
    async evaluation pipeline via `asyncio.run` per newly created submission.
    """
    db = SessionLocal()
    try:
        result = sync_submissions(db)
        logger.info(
            "Google Forms sync complete: created=%d skipped_duplicate=%d unmatched_email=%d",
            result["created"],
            result["skipped_duplicate"],
            result["unmatched_email"],
        )

        for submission in result["created_submissions"]:
            try:
                asyncio.run(run_evaluation_for_submission(submission.id))
            except Exception:
                logger.exception(
                    "Evaluation failed for submission_id=%s during scheduled sync",
                    submission.id,
                )
    except Exception:
        logger.exception("Google Forms sync job failed")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    """Create, configure, and start the background scheduler. Idempotent."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_sync_job,
        "interval",
        minutes=settings.GOOGLE_FORMS_SYNC_INTERVAL_MINUTES,
        id=JOB_ID,
        replace_existing=True,
        max_instances=1,  # prevent overlapping runs if sync takes longer than the interval
    )
    _scheduler.start()
    logger.info(
        "Started Google Forms sync scheduler (interval=%d minutes)",
        settings.GOOGLE_FORMS_SYNC_INTERVAL_MINUTES,
    )
    return _scheduler


def stop_scheduler() -> None:
    """Shut down the background scheduler if it is running."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Stopped Google Forms sync scheduler")
    _scheduler = None
