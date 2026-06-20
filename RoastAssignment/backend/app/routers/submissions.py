"""Submission endpoints: list, detail, manual creation, and Google Forms sync trigger."""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.exceptions import ForbiddenError, NotFoundError
from app.models.submission import SyncStatus, Submission
from app.models.user import User, UserRole
from app.schemas.submission import (
    SubmissionCreateRequest,
    SubmissionResponse,
    SubmissionWithEvaluation,
)
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


@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    data: SubmissionCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("student")),
) -> Submission:
    """Let a student submit a GitHub repo for evaluation directly from the app.

    This is the manual-entry counterpart to the Google Forms sync: the
    submission is already matched to `user` (the authenticated student), so
    it's created with `sync_status=synced` and evaluation is dispatched
    immediately as a background task.
    """
    submission = Submission(
        user_id=user.id,
        student_name=user.full_name or user.email,
        student_email=user.email,
        assignment_name=data.assignment_name,
        github_repo_url=data.github_repo_url,
        google_form_response_id=f"manual-{uuid4()}",
        sync_status=SyncStatus.synced,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    background_tasks.add_task(run_evaluation_for_submission, submission.id)
    return submission


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
