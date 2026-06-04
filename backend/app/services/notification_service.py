from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.notification_repository import NotificationRepository
from backend.app.core.exceptions import NotFoundError
from uuid import UUID


class NotificationService:
    @staticmethod
    async def list_notifications(
        db: AsyncSession, workspace_id: UUID, skip: int = 0, limit: int = 50, unread_only: bool = False
    ):
        return await NotificationRepository.list_by_workspace(
            db, workspace_id, skip, limit, unread_only
        )

    @staticmethod
    async def mark_as_read(db: AsyncSession, notification_id: UUID, workspace_id: UUID):
        success = await NotificationRepository.mark_as_read(db, notification_id, workspace_id)
        if not success:
            raise NotFoundError("Notification not found")
        return True

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, workspace_id: UUID):
        count = await NotificationRepository.mark_all_as_read(db, workspace_id)
        return count
