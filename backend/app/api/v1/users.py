from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.schemas.user import UserUpdate, UserRoleUpdate
from backend.app.controllers.user_controller import UserController
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id, require_admin
from backend.app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/me")
async def update_profile(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await UserController.update_profile(db, current_user.id, data)


@router.put("/{target_user_id}/role")
async def update_role(
    target_user_id: UUID,
    data: UserRoleUpdate,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await UserController.update_role(db, target_user_id, workspace_id, data)

