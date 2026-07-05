"""Admin panel endpoints - all require the admin role."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_role
from app.schemas.admin import AdminStatsResponse, AdminUserResponse, AdminUserUpdateRequest
from app.services.admin_service import get_platform_stats, list_all_users, update_user

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])


@router.get("/users", response_model=list[AdminUserResponse])
async def get_users(db: Session = Depends(get_db)) -> list[AdminUserResponse]:
    """List every user account on the platform."""
    users = list_all_users(db)
    return [AdminUserResponse.model_validate(user) for user in users]


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def put_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    """Update a user's role and/or active status."""
    user = update_user(db, user_id, payload)
    return AdminUserResponse.model_validate(user)


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(db: Session = Depends(get_db)) -> AdminStatsResponse:
    """Return platform-wide statistics."""
    return get_platform_stats(db)
