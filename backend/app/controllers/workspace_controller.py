from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.workspace_service import WorkspaceService
from backend.app.schemas.workspace import (
    WorkspaceResponse,
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest,
    WorkspaceStatsResponse,
    WorkspaceMemberResponse,
)
from backend.app.core.response import success_response
from uuid import UUID


class WorkspaceController:
    @staticmethod
    async def create_workspace(db: AsyncSession, user_id: UUID, create_data: WorkspaceCreateRequest) -> dict:
        workspace = await WorkspaceService.create_workspace(db, user_id, create_data)
        workspace_resp = WorkspaceResponse.model_validate(workspace)
        return success_response(workspace_resp.model_dump())

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
    async def get_members(db: AsyncSession, workspace_id: UUID) -> dict:
        members = await WorkspaceService.get_members(db, workspace_id)
        members_resp = [
            WorkspaceMemberResponse(
                id=m.id,
                user_id=m.user_id,
                workspace_id=m.workspace_id,
                role=m.role,
                user_email=m.user.email if m.user else "",
                user_name=m.user.full_name if m.user else "",
            ).model_dump()
            for m in members
        ]
        return success_response(members_resp)

    @staticmethod
    async def get_stats(db: AsyncSession, workspace_id: UUID) -> dict:
        stats = await WorkspaceService.get_stats(db, workspace_id)
        stats_resp = WorkspaceStatsResponse.model_validate(stats)
        return success_response(stats_resp.model_dump())

    @staticmethod
    async def delete_workspace(db: AsyncSession, workspace_id: UUID, user_id: UUID) -> dict:
        await WorkspaceService.delete_workspace(db, workspace_id, user_id)
        return success_response({"deleted": True})
