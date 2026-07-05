"""Fee structure management endpoints.

Access rules (CLAUDE.md):
  - Teachers manage fee structures for their own students only.
  - Parents may view (not write) fees for their own linked children.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.fee import (
    FeeDetailResponse,
    FeeGenerationSummaryResponse,
    FeeStructureCreate,
    FeeStructureResponse,
    FeeStructureUpdate,
    FeeStructureWithBalance,
)
from app.services import fee_service

router = APIRouter(prefix="/fees", tags=["fees"])


@router.get("/overdue", response_model=list[FeeStructureWithBalance])
async def get_overdue_fees(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> list[FeeStructureWithBalance]:
    """List overdue fees (with outstanding balance) for the teacher's own students."""
    return fee_service.list_overdue_fees(db, current_user)


@router.get("/students/{student_id}", response_model=FeeDetailResponse)
async def get_student_fees(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeeDetailResponse:
    """Fee structures + payment history + outstanding balance for a student. Role-scoped."""
    return fee_service.get_fee_detail(db, current_user, student_id)


@router.post("", response_model=FeeStructureResponse, status_code=status.HTTP_201_CREATED)
async def create_fee_structure(
    payload: FeeStructureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> FeeStructureResponse:
    """Create a fee structure. Teacher-only; ownership-checked."""
    return fee_service.create_fee_structure(db, current_user, payload)


@router.put("/{fee_id}", response_model=FeeStructureResponse)
async def update_fee_structure(
    fee_id: int,
    payload: FeeStructureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> FeeStructureResponse:
    """Update a fee structure. Teacher-only; ownership-checked."""
    return fee_service.update_fee_structure(db, current_user, fee_id, payload)


@router.post("/generate-from-attendance", response_model=FeeGenerationSummaryResponse)
async def generate_fees_from_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> FeeGenerationSummaryResponse:
    """Auto-generate monthly fee structures from past-month attendance. Teacher-only."""
    return fee_service.generate_fees_from_attendance(db, current_user.id)


@router.post("/{fee_id}/remind", status_code=status.HTTP_202_ACCEPTED)
async def remind(
    fee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> dict[str, str]:
    """Manually trigger a fee reminder email for an overdue fee. Teacher-only."""
    fee_service.send_reminder(db, current_user, fee_id)
    return {"detail": "Reminder sent"}


@router.post("/{fee_id}/mark-paid", response_model=FeeStructureWithBalance)
async def mark_fee_paid(
    fee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.teacher)),
) -> FeeStructureWithBalance:
    """Manually record a fee as fully paid (cash/offline payment). Teacher-only."""
    return fee_service.mark_fee_paid(db, current_user, fee_id)
