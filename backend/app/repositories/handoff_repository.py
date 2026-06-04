from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List, Optional

from backend.app.models.handoff import Handoff
from backend.app.models.conversation import Conversation


class HandoffRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        conversation_id: UUID,
        from_agent: str,
        to_agent: str,
        reason: str,
        confidence: float
    ) -> Handoff:
        # We append confidence to reason for now, as DB schema reason is Text
        reason_with_conf = f"{reason} (Confidence: {confidence:.2f})"
        
        db_obj = Handoff(
            conversation_id=conversation_id,
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason_with_conf,
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_conversation(
        db: AsyncSession, conversation_id: UUID
    ) -> List[Handoff]:
        result = await db.execute(
            select(Handoff)
            .where(Handoff.conversation_id == conversation_id)
            .order_by(Handoff.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_conversation_agent(
        db: AsyncSession, conversation_id: UUID, agent: str
    ) -> Optional[Conversation]:
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conv = result.scalars().first()
        if conv:
            conv.current_agent = agent
            db.add(conv)
            await db.flush()
        return conv
