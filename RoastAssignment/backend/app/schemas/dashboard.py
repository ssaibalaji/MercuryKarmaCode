"""Pydantic schemas for dashboard/stats endpoints."""
from typing import Optional

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Role-scoped summary counts for the dashboard landing view."""

    total_submissions: int
    pending_evaluations: int
    completed_evaluations: int
    failed_evaluations: int
    average_overall_score: Optional[float] = None

    class Config:
        from_attributes = True


class ScoreDistributionBucket(BaseModel):
    """One bucket of the overall-score histogram (e.g. "0.2-0.4")."""

    range: str
    count: int

    class Config:
        from_attributes = True


class SubmissionsOverTimePoint(BaseModel):
    """Number of submissions received on a given calendar day."""

    date: str
    count: int

    class Config:
        from_attributes = True
