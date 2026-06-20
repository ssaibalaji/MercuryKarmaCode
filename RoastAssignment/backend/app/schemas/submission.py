"""Pydantic schemas for submission endpoints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class SubmissionResponse(BaseModel):
    """Public-facing representation of a submission."""

    id: int
    user_id: int
    student_name: str
    student_email: EmailStr
    assignment_name: str
    github_repo_url: str
    google_form_response_id: str
    sync_status: str
    submitted_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("sync_status", mode="before")
    @classmethod
    def _coerce_sync_status(cls, value: object) -> str:
        """Accept the SQLAlchemy `SyncStatus` enum member and coerce to its value."""
        return value.value if hasattr(value, "value") else value


class EvaluationSummary(BaseModel):
    """Minimal evaluation summary nested inside `SubmissionWithEvaluation`."""

    id: int
    status: str
    overall_score: Optional[float]
    evaluated_at: Optional[datetime]

    class Config:
        from_attributes = True

    @field_validator("status", mode="before")
    @classmethod
    def _coerce_status(cls, value: object) -> str:
        """Accept the SQLAlchemy `EvaluationStatus` enum member and coerce to its value."""
        return value.value if hasattr(value, "value") else value


class SubmissionWithEvaluation(SubmissionResponse):
    """Submission detail view including its (optional) evaluation summary."""

    evaluation: Optional[EvaluationSummary] = None


# `SubmissionListResponse` is intentionally just `list[SubmissionResponse]`; routers
# use that directly as the `response_model` instead of a wrapper object.
