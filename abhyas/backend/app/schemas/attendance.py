"""Pydantic schemas for the attendance module."""
from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.attendance import AttendanceStatus


class AttendanceEntry(BaseModel):
    """A single student's attendance mark for a given date - the unit used both
    for a lone mark and as an item within a bulk (class/day) mark request."""

    student_id: int
    date: date_type
    status: AttendanceStatus
    notes: str | None = Field(default=None, max_length=500)


class AttendanceMarkRequest(BaseModel):
    """Payload for POST /attendance.

    Supports marking a single student (`entries` has one item) or an entire
    class/section for a day (`entries` has many items) in one request.
    """

    entries: list[AttendanceEntry] = Field(min_length=1)


class AttendanceUpdateRequest(BaseModel):
    """Payload for PUT /attendance/{id} - only status/notes are editable."""

    status: AttendanceStatus | None = None
    notes: str | None = Field(default=None, max_length=500)


class AttendanceResponse(BaseModel):
    """Public-facing representation of an AttendanceRecord."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    teacher_id: int
    date: date_type
    status: AttendanceStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class AttendanceSummaryResponse(BaseModel):
    """Attendance percentage + breakdown summary for a single student."""

    student_id: int
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    attendance_percentage: float


class CalendarDaySummary(BaseModel):
    """Per-date present/absent/late breakdown for the calendar view."""

    date: date_type
    present: int
    absent: int
    late: int
    total: int


class CalendarSummaryResponse(BaseModel):
    """A month's worth of per-day attendance breakdowns."""

    days: list[CalendarDaySummary]
