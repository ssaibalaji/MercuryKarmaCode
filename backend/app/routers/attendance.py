"""API endpoints for marking, querying, and summarizing attendance."""
from datetime import date as date_type

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_role
from app.models.user import User
from app.schemas.attendance import (
    AttendanceMarkRequest,
    AttendanceResponse,
    AttendanceSummaryResponse,
    AttendanceUpdateRequest,
    CalendarSummaryResponse,
)
from app.services import attendance_service

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("", response_model=list[AttendanceResponse])
async def list_attendance(
    date: date_type | None = None,
    class_grade: str | None = None,
    student_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AttendanceResponse]:
    """Query attendance, scoped to the current user's role.

    Teachers see their own students' records; parents see their linked
    children's records; optional filters narrow further.
    """
    records = attendance_service.query_attendance(
        db, current_user, date=date, class_grade=class_grade, student_id=student_id
    )
    return [AttendanceResponse.model_validate(record) for record in records]


@router.post("", response_model=list[AttendanceResponse], status_code=status.HTTP_201_CREATED)
async def mark_attendance(
    payload: AttendanceMarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("teacher")),
) -> list[AttendanceResponse]:
    """Mark attendance for one or many students on one or many dates (upsert).

    Re-marking the same (student_id, date) pair updates the existing record
    rather than raising a conflict.
    """
    records = attendance_service.bulk_mark_attendance(db, payload.entries, current_user)
    return [AttendanceResponse.model_validate(record) for record in records]


@router.put("/{record_id}", response_model=AttendanceResponse)
async def update_attendance(
    record_id: int,
    payload: AttendanceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("teacher")),
) -> AttendanceResponse:
    """Update an existing attendance record. Only the owning teacher may do so."""
    record = attendance_service.update_attendance(
        db, record_id, current_user, status=payload.status, notes=payload.notes
    )
    return AttendanceResponse.model_validate(record)


@router.get("/calendar-summary", response_model=CalendarSummaryResponse)
async def get_calendar_summary(
    year: int | None = Query(default=None, ge=1),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("teacher")),
) -> CalendarSummaryResponse:
    """Per-day present/absent/late/total breakdown for a month, scoped to the
    current teacher's own students. Defaults to the current year/month.
    """
    today = date_type.today()
    resolved_year = year if year is not None else today.year
    resolved_month = month if month is not None else today.month
    return attendance_service.get_calendar_summary(
        db, current_user, resolved_year, resolved_month
    )


@router.get("/student/{student_id}/summary", response_model=AttendanceSummaryResponse)
async def get_student_summary(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttendanceSummaryResponse:
    """Attendance percentage + present/absent/late breakdown for one student.

    Readable by the owning teacher, the linked parent, or an admin.
    """
    return attendance_service.get_attendance_summary(db, current_user, student_id)
