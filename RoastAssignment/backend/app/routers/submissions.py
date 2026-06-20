"""Submission endpoints: list, detail, and manual Google Forms sync trigger."""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.exceptions import ForbiddenError, NotFoundError
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.schemas.submission import SubmissionResponse, SubmissionWithEvaluation
from app.services.evaluation_service import run_evaluation_for_submission
from app.services.google_forms_sync import sync_submissions

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("/", response_model=list[SubmissionResponse])
async def list_submissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Submission]:
    """List submissions: students see only their own, examiners/coaches see all."""
    query = db.query(Submission)
    if user.role == UserRole.student:
        query = query.filter(Submission.user_id == user.id)

    return (
        query.order_by(Submission.submitted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{submission_id}", response_model=SubmissionWithEvaluation)
async def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Submission:
    """Get a single submission with its evaluation summary, if any."""
    submission = (
        db.query(Submission)
        .options(joinedload(Submission.evaluation))
        .filter(Submission.id == submission_id)
        .first()
    )
    if submission is None:
        raise NotFoundError("Submission")

    if user.role == UserRole.student and submission.user_id != user.id:
        raise ForbiddenError("You do not have access to this submission")

    return submission


@router.post("/sync")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("examiner", "coach")),
) -> dict:
    """Manually trigger a Google Forms sync and dispatch evaluation for new submissions."""
    result = sync_submissions(db)

    for submission in result["created_submissions"]:
        background_tasks.add_task(run_evaluation_for_submission, submission.id)

    return {
        "created": result["created"],
        "skipped_duplicate": result["skipped_duplicate"],
        "unmatched_email": result["unmatched_email"],
    }
