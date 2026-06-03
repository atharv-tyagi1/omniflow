from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.handoff import Handoff

class HandoffRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        conversation_id: UUID,
        from_agent: str,
        to_agent: str,
        reason: str = None
    ) -> Handoff:
        handoff = Handoff(
            conversation_id=conversation_id,
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason
        )
        db.add(handoff)
        await db.commit()
        await db.refresh(handoff)
        return handoff
