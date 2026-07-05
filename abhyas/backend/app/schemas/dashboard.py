"""Pydantic schemas for the teacher dashboard module."""
from datetime import date, datetime

from pydantic import BaseModel


class RecentActivityEntry(BaseModel):
    """A single entry in the dashboard's recent-activity feed."""

    type: str
    description: str
    timestamp: datetime


class DashboardStatsResponse(BaseModel):
    """Aggregated statistics shown on a teacher's dashboard."""

    total_students: int
    attendance_percentage_recent: float
    attendance_reference_date: date
    overdue_fees_count: int
    total_fees_collected_this_month: float
    recent_activity: list[RecentActivityEntry]
