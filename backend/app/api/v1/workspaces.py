from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from backend.app.core.database import get_db
from backend.app.schemas.workspace import WorkspaceCreateRequest, WorkspaceUpdateRequest
from backend.app.controllers.workspace_controller import WorkspaceController
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import (
    get_current_workspace_id,
    require_admin,
)
from backend.app.models.user import User

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("")
async def create_workspace(
    create_data: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceController.create_workspace(db, current_user.id, create_data)


@router.get("/current")
async def get_current_workspace(
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceController.get_workspace(db, workspace_id)


@router.put("/current")
async def update_current_workspace(
    update_data: WorkspaceUpdateRequest,
    current_user: User = Depends(
        require_admin
    ),  # requires admin or owner to update settings
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceController.update_workspace(db, workspace_id, update_data)


@router.get("/members")
async def get_workspace_members(
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceController.get_members(db, workspace_id)


@router.get("/stats")
async def get_workspace_statistics(
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceController.get_stats(db, workspace_id)

@router.delete("/current")
async def delete_current_workspace(
    current_user: User = Depends(require_admin), # We enforce owner strictly at the service layer, but require at least admin here to pass the guard
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceController.delete_workspace(db, workspace_id, current_user.id)
