from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.workspace_repository import WorkspaceRepository
from backend.app.core.exceptions import NotFoundError
from backend.app.schemas.workspace import WorkspaceUpdateRequest
from uuid import UUID

class WorkspaceService:
    @staticmethod
    async def get_workspace(db: AsyncSession, workspace_id: UUID):
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")
        return workspace

    @staticmethod
    async def update_workspace(db: AsyncSession, workspace_id: UUID, update_data: WorkspaceUpdateRequest):
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")
        
        # Clean request data
        update_dict = update_data.model_dump(exclude_unset=True)
        
        return await WorkspaceRepository.update(db, db_obj=workspace, obj_in=update_dict)

    @staticmethod
    async def get_stats(db: AsyncSession, workspace_id: UUID):
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")
        return await WorkspaceRepository.get_stats(db, workspace_id)
