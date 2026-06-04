from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.user_service import UserService
from backend.app.schemas.user import UserUpdate, UserRoleUpdate
from backend.app.core.response import success_response
from uuid import UUID


class UserController:
    @staticmethod
    async def update_profile(db: AsyncSession, user_id: UUID, data: UserUpdate) -> dict:
        user = await UserService.update_profile(db, user_id, data)
        return success_response({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url
        })

    @staticmethod
    async def update_role(
        db: AsyncSession, target_user_id: UUID, workspace_id: UUID, data: UserRoleUpdate
    ) -> dict:
        membership = await UserService.update_role(db, target_user_id, workspace_id, data)
        return success_response({
            "user_id": membership.user_id,
            "role": membership.role
        })
