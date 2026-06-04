from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.workspace_member_repository import WorkspaceMemberRepository
from backend.app.schemas.user import UserUpdate, UserRoleUpdate
from backend.app.core.exceptions import NotFoundError, BusinessRuleError
from uuid import UUID


class UserService:
    @staticmethod
    async def update_profile(db: AsyncSession, user_id: UUID, data: UserUpdate):
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            raise NotFoundError("User not found")

        update_data = data.model_dump(exclude_unset=True)
        return await UserRepository.update(db, db_obj=user, obj_in=update_data)

    @staticmethod
    async def update_role(
        db: AsyncSession, target_user_id: UUID, workspace_id: UUID, data: UserRoleUpdate
    ):
        """Update a user's role within a specific workspace."""
        membership = await WorkspaceMemberRepository.get_by_user_and_workspace(
            db, target_user_id, workspace_id
        )
        if not membership:
            raise NotFoundError("User is not a member of this workspace")
        
        # Enforce that there must always be at least one owner
        if membership.role == "owner" and data.role != "owner":
            # Check if they are the last owner
            all_members = await WorkspaceMemberRepository.get_members_for_workspace(db, workspace_id)
            owners = [m for m in all_members if m.role == "owner"]
            if len(owners) <= 1:
                raise BusinessRuleError("Cannot change role of the last owner in the workspace")

        membership.role = data.role
        db.add(membership)
        await db.flush()
        return membership
