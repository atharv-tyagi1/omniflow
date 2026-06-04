from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from uuid import UUID
from typing import Optional

from backend.app.models.notification import Notification


class NotificationRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        title: str,
        message: Optional[str] = None,
        type: str = "info"
    ) -> Notification:
        db_obj = Notification(
            workspace_id=workspace_id, title=title, message=message, type=type
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_id(
        db: AsyncSession, notification_id: UUID, workspace_id: UUID
    ) -> Optional[Notification]:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.workspace_id == workspace_id,
            )
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_workspace(
        db: AsyncSession, workspace_id: UUID, skip: int = 0, limit: int = 50, unread_only: bool = False
    ) -> list[Notification]:
        query = select(Notification).where(Notification.workspace_id == workspace_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def mark_as_read(
        db: AsyncSession, notification_id: UUID, workspace_id: UUID
    ) -> bool:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.workspace_id == workspace_id,
            )
        )
        notif = result.scalars().first()
        if notif:
            notif.is_read = True
            db.add(notif)
            await db.flush()
            return True
        return False

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, workspace_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(Notification.workspace_id == workspace_id, Notification.is_read == False)
            .values(is_read=True)
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.rowcount
