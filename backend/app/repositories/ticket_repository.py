from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional

from backend.app.models.ticket import Ticket


class TicketRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium"
    ) -> Ticket:
        db_obj = Ticket(
            workspace_id=workspace_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            title=title,
            description=description,
            priority=priority,
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_id(
        db: AsyncSession, ticket_id: UUID, workspace_id: UUID
    ) -> Optional[Ticket]:
        result = await db.execute(
            select(Ticket).where(
                Ticket.id == ticket_id, Ticket.workspace_id == workspace_id
            )
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_workspace(
        db: AsyncSession, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Ticket]:
        result = await db.execute(
            select(Ticket).where(Ticket.workspace_id == workspace_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, *, db_obj: Ticket, obj_in: dict) -> Ticket:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.flush()
        return db_obj
