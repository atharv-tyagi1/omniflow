from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.workspace_repository import WorkspaceRepository
from backend.app.repositories.workspace_member_repository import WorkspaceMemberRepository
from backend.app.core.exceptions import NotFoundError
from backend.app.schemas.workspace import WorkspaceUpdateRequest, WorkspaceCreateRequest
from uuid import UUID


class WorkspaceService:
    @staticmethod
    async def create_workspace(
        db: AsyncSession, user_id: UUID, create_data: WorkspaceCreateRequest
    ):
        """Create a new workspace and assign the requesting user as owner."""
        workspace = await WorkspaceRepository.create(
            db, name=create_data.name, industry=create_data.industry
        )

        # Add the creating user as workspace owner
        await WorkspaceMemberRepository.create(
            db, workspace_id=workspace.id, user_id=user_id, role="owner"
        )

        return workspace

    @staticmethod
    async def get_workspace(db: AsyncSession, workspace_id: UUID):
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")
        return workspace

    @staticmethod
    async def update_workspace(
        db: AsyncSession, workspace_id: UUID, update_data: WorkspaceUpdateRequest
    ):
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        update_dict = update_data.model_dump(exclude_unset=True)

        return await WorkspaceRepository.update(
            db, db_obj=workspace, obj_in=update_dict
        )

    @staticmethod
    async def get_members(db: AsyncSession, workspace_id: UUID):
        """Return all members of a workspace with their roles."""
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")

        members = await WorkspaceMemberRepository.get_members_for_workspace(db, workspace_id)
        return members

    @staticmethod
    async def get_stats(db: AsyncSession, workspace_id: UUID):
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")
        return await WorkspaceRepository.get_stats(db, workspace_id)

    @staticmethod
    async def delete_workspace(db: AsyncSession, workspace_id: UUID, user_id: UUID):
        """
        Safely delete a workspace.
        This cascades to all tenant data because of ondelete='CASCADE' in models.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        workspace = await WorkspaceRepository.get(db, workspace_id)
        if not workspace:
            raise NotFoundError("Workspace not found")
            
        logger.warning(f"SECURITY AUDIT: User {user_id} is attempting to delete Workspace {workspace_id} ({workspace.name})")
        
        # Verify user is actually an owner
        membership = await WorkspaceMemberRepository.get_by_user_and_workspace(db, user_id, workspace_id)
        if not membership or membership.role != "owner":
            logger.error(f"SECURITY AUDIT: User {user_id} denied deleting Workspace {workspace_id} - Not an owner")
            from backend.app.core.exceptions import BusinessRuleError
            raise BusinessRuleError("Only workspace owners can delete the workspace.")
            
        success = await WorkspaceRepository.delete(db, workspace_id)
        if success:
            logger.warning(f"SECURITY AUDIT: Workspace {workspace_id} successfully deleted by User {user_id}")
        return success
