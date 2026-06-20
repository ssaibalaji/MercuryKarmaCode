"""Role-scoped dashboard/stats endpoints for the Assignment Evaluator."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    DashboardStats,
    ScoreDistributionBucket,
    SubmissionsOverTimePoint,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Overall scores are stored on a 0-1 scale (see app/models/evaluation.py).
_SCORE_BUCKET_EDGES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DashboardStats:
    """Summary counts for the dashboard landing view.

    Students see only their own submissions; examiners/coaches see totals
    across all submissions.
    """
    submissions_query = db.query(Submission)
    status_query = db.query(
        Evaluation.status, func.count(Evaluation.id)
    ).join(Submission, Submission.id == Evaluation.submission_id)
    avg_query = db.query(func.avg(Evaluation.overall_score)).join(
        Submission, Submission.id == Evaluation.submission_id
    )

    if user.role == UserRole.student:
        submissions_query = submissions_query.filter(Submission.user_id == user.id)
        status_query = status_query.filter(Submission.user_id == user.id)
        avg_query = avg_query.filter(Submission.user_id == user.id)

    total_submissions = submissions_query.with_entities(
        func.count(Submission.id)
    ).scalar() or 0

    status_counts = dict(status_query.group_by(Evaluation.status).all())
    pending_evaluations = status_counts.get(EvaluationStatus.pending, 0) + status_counts.get(
        EvaluationStatus.running, 0
    )
    completed_evaluations = status_counts.get(EvaluationStatus.completed, 0)
    failed_evaluations = status_counts.get(EvaluationStatus.failed, 0)

    average_overall_score = avg_query.filter(
        Evaluation.status == EvaluationStatus.completed
    ).scalar()

    return DashboardStats(
        total_submissions=total_submissions,
        pending_evaluations=pending_evaluations,
        completed_evaluations=completed_evaluations,
        failed_evaluations=failed_evaluations,
        average_overall_score=(
            float(average_overall_score) if average_overall_score is not None else None
        ),
    )


@router.get(
    "/analytics/score-distribution",
    response_model=list[ScoreDistributionBucket],
)
async def get_score_distribution(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("examiner", "coach")),
) -> list[ScoreDistributionBucket]:
    """Histogram of completed evaluations' `overall_score` (0-1 scale, 0.2-wide buckets)."""
    rows = (
        db.query(Evaluation.overall_score)
        .filter(
            Evaluation.status == EvaluationStatus.completed,
            Evaluation.overall_score.isnot(None),
        )
        .all()
    )

    edges = _SCORE_BUCKET_EDGES
    counts = [0] * (len(edges) - 1)
    for (score,) in rows:
        if score is None:
            continue
        # Clamp to the valid range, then bucket; the top edge (1.0) belongs to the last bucket.
        clamped = min(max(score, edges[0]), edges[-1])
        idx = min(int((clamped - edges[0]) / (edges[-1] - edges[0]) * len(counts)), len(counts) - 1)
        counts[idx] += 1

    return [
        ScoreDistributionBucket(range=f"{edges[i]:.1f}-{edges[i + 1]:.1f}", count=counts[i])
        for i in range(len(counts))
    ]


@router.get(
    "/analytics/submissions-over-time",
    response_model=list[SubmissionsOverTimePoint],
)
async def get_submissions_over_time(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("examiner", "coach")),
) -> list[SubmissionsOverTimePoint]:
    """Daily submission counts for the last 30 days, grouped by `Submission.submitted_at` date."""
    since = datetime.now(timezone.utc) - timedelta(days=30)
    day = func.date(Submission.submitted_at)

    rows = (
        db.query(day.label("day"), func.count(Submission.id))
        .filter(Submission.submitted_at >= since)
        .group_by(day)
        .order_by(day)
        .all()
    )

    return [
        SubmissionsOverTimePoint(date=str(day_value), count=count)
        for day_value, count in rows
    ]
