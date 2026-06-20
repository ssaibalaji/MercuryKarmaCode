"""Pydantic schemas for evaluation endpoints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class EvaluationResponse(BaseModel):
    """Public-facing representation of an evaluation."""

    id: int
    submission_id: int
    ai_roast_text: Optional[str]
    ai_score: Optional[float]
    static_analysis_report: Optional[dict]
    static_analysis_score: Optional[float]
    overall_score: Optional[float]
    status: str
    evaluated_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("status", mode="before")
    @classmethod
    def _coerce_status(cls, value: object) -> str:
        """Accept the SQLAlchemy `EvaluationStatus` enum member and coerce to its value."""
        return value.value if hasattr(value, "value") else value


class EvaluationCommentRequest(BaseModel):
    """Body for the PUT override endpoint that lets an examiner/coach attach a comment.

    NOTE (limitation): the `Evaluation` model has no `comment` column yet (adding one
    would require a second Alembic migration this agent isn't running). Per the task
    spec we deliberately picked the simpler, non-persisting option: the router accepts
    this body, attaches the comment to the *response only* (it is never written to the
    database), and documents that limitation. A follow-up migration + model field would
    be needed to actually persist examiner comments.
    """

    comment: str
