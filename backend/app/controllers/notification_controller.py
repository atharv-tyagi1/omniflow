from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.notification_service import NotificationService
from backend.app.schemas.notification import NotificationResponse
from backend.app.core.response import success_response
from uuid import UUID


class NotificationController:
    @staticmethod
    async def list_notifications(
        db: AsyncSession, workspace_id: UUID, skip: int = 0, limit: int = 50, unread_only: bool = False
    ) -> dict:
        notifications = await NotificationService.list_notifications(
            db, workspace_id, skip, limit, unread_only
        )
        return success_response(
            [NotificationResponse.model_validate(n).model_dump() for n in notifications]
        )

    @staticmethod
    async def mark_as_read(
        db: AsyncSession, notification_id: UUID, workspace_id: UUID
    ) -> dict:
        await NotificationService.mark_as_read(db, notification_id, workspace_id)
        return success_response({"marked_read": True})

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, workspace_id: UUID) -> dict:
        count = await NotificationService.mark_all_as_read(db, workspace_id)
        return success_response({"marked_read": True, "count": count})
