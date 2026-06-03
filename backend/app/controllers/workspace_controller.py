from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.workspace_service import WorkspaceService
from backend.app.schemas.workspace import (
    WorkspaceResponse,
    WorkspaceUpdateRequest,
    WorkspaceStatsResponse,
)
from backend.app.core.response import success_response
from uuid import UUID


class WorkspaceController:
    @staticmethod
    async def get_workspace(db: AsyncSession, workspace_id: UUID) -> dict:
        workspace = await WorkspaceService.get_workspace(db, workspace_id)
        workspace_resp = WorkspaceResponse.model_validate(workspace)
        return success_response(workspace_resp.model_dump())

    @staticmethod
    async def update_workspace(
        db: AsyncSession, workspace_id: UUID, update_data: WorkspaceUpdateRequest
    ) -> dict:
        workspace = await WorkspaceService.update_workspace(
            db, workspace_id, update_data
        )
        workspace_resp = WorkspaceResponse.model_validate(workspace)
        return success_response(workspace_resp.model_dump())

    @staticmethod
    async def get_stats(db: AsyncSession, workspace_id: UUID) -> dict:
        stats = await WorkspaceService.get_stats(db, workspace_id)
        stats_resp = WorkspaceStatsResponse.model_validate(stats)
        return success_response(stats_resp.model_dump())
