"""Evaluation endpoints: fetch result, retry, and (non-persisted) examiner comment."""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.exceptions import ForbiddenError, NotFoundError
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.schemas.evaluation import EvaluationCommentRequest, EvaluationResponse
from app.services.evaluation_service import run_evaluation_for_submission

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def _get_evaluation_or_404(db: Session, submission_id: int) -> Evaluation:
    evaluation = (
        db.query(Evaluation).filter(Evaluation.submission_id == submission_id).first()
    )
    if evaluation is None:
        raise NotFoundError("Evaluation")
    return evaluation


@router.get("/{submission_id}", response_model=EvaluationResponse)
async def get_evaluation(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Evaluation:
    """Get the evaluation for a submission.

    Students may only view evaluations for their own submissions; examiners/coaches
    may view any.
    """
    evaluation = _get_evaluation_or_404(db, submission_id)

    if user.role == UserRole.student:
        submission = (
            db.query(Submission).filter(Submission.id == submission_id).first()
        )
        if submission is None or submission.user_id != user.id:
            raise ForbiddenError("You do not have access to this evaluation")

    return evaluation


@router.post("/{submission_id}/retry")
async def retry_evaluation(
    submission_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("examiner", "coach")),
) -> dict:
    """Re-run the evaluation pipeline for a submission in the background."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if submission is None:
        raise NotFoundError("Submission")

    background_tasks.add_task(run_evaluation_for_submission, submission_id)
    return {"status": "retry_scheduled"}


@router.put("/{submission_id}", response_model=EvaluationResponse)
async def add_evaluation_comment(
    submission_id: int,
    data: EvaluationCommentRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("examiner", "coach")),
) -> EvaluationResponse:
    """Attach an examiner/coach comment to an evaluation's response.

    LIMITATION: `Evaluation` has no `comment` column today (adding one needs a
    migration this endpoint doesn't run). The comment is therefore NOT persisted
    to the database. We deliberately avoid mutating the ORM-tracked `Evaluation`
    instance (mutating it could get accidentally flushed/committed by some other
    code path sharing the session) and instead build a fresh `EvaluationResponse`
    with the note appended to `ai_roast_text`, returned only for this single
    request/response cycle. A subsequent GET will not show the comment. A real
    implementation would add an `Evaluation.comment` column + migration.
    """
    evaluation = _get_evaluation_or_404(db, submission_id)

    response = EvaluationResponse.model_validate(evaluation)
    note = f"\n\nExaminer note: {data.comment}"
    response.ai_roast_text = (response.ai_roast_text or "") + note

    return response
