"""Student management endpoints.

Access rules (CLAUDE.md):
  - Teachers: full CRUD on their own students (teacher_id == current_user.id).
  - Parents: read-only, limited to students where parent_user_id == current_user.id.
  - Admins: not served by this router (use /admin/*).
"""
from datetime import date as date_type

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.student import (
    MonthlyFeePreviewResponse,
    ParentInviteRequest,
    ParentInviteResponse,
    StudentCreate,
    StudentListItem,
    StudentResponse,
    StudentUpdate,
)
from app.services import student_service

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentListItem])
async def list_students(
    class_grade: str | None = None,
    section: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StudentListItem]:
    """List students visible to the current user (role-filtered)."""
    return student_service.get_students_for_user(
        db, current_user, class_grade=class_grade, section=section
    )


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> StudentResponse:
    """Create a new student. Teacher-only; teacher_id is set from the token."""
    return student_service.create_student(db, current_user, payload)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentResponse:
    """Fetch a single student. Ownership/linkage-checked."""
    return student_service.get_student_by_id(db, student_id, current_user)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> StudentResponse:
    """Update a student. Teacher-only; ownership-checked."""
    return student_service.update_student(db, student_id, current_user, payload)


@router.delete("/{student_id}", response_model=StudentResponse)
async def deactivate_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> StudentResponse:
    """Soft-delete (deactivate) a student. Teacher-only; ownership-checked."""
    return student_service.deactivate_student(db, student_id, current_user)


@router.get("/{student_id}/monthly-fee", response_model=MonthlyFeePreviewResponse)
async def get_monthly_fee_preview(
    student_id: int,
    year: int | None = Query(default=None, ge=1),
    month: int | None = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonthlyFeePreviewResponse:
    """Preview the calculated monthly fee for an arbitrary month, without
    persisting anything. Defaults to the current year/month. Readable by the
    owning teacher or the linked parent.
    """
    today = date_type.today()
    resolved_year = year if year is not None else today.year
    resolved_month = month if month is not None else today.month

    calculated = student_service.get_monthly_fee_preview(
        db, student_id, current_user, resolved_year, resolved_month
    )
    return MonthlyFeePreviewResponse(
        year=resolved_year,
        month=resolved_month,
        calculated_monthly_fee=str(calculated),
    )


@router.post("/{student_id}/invite-parent", response_model=ParentInviteResponse)
async def invite_parent(
    student_id: int,
    payload: ParentInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> ParentInviteResponse:
    """Invite a parent to link to a student. Teacher-only; ownership-checked.

    See app.services.student_service.invite_parent for the current (email-less)
    invite behavior pending the Auth module's email service.
    """
    student, invited, parent_user_id, message = student_service.invite_parent(
        db, student_id, current_user, payload.parent_email, payload.parent_name
    )
    return ParentInviteResponse(
        student_id=student.id,
        parent_email=payload.parent_email,
        invited=invited,
        parent_user_id=parent_user_id,
        message=message,
    )
