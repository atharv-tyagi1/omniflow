"""Router Event Repository — handles DB operations for router metrics."""

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from backend.app.models.router_event import RouterEvent


class RouterEventRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        conversation_id: UUID,
        primary_intent: str,
        secondary_intent: Optional[str],
        confidence: float,
        decision: str,
        routed_agent: Optional[str],
    ) -> RouterEvent:
        db_obj = RouterEvent(
            conversation_id=conversation_id,
            primary_intent=primary_intent,
            secondary_intent=secondary_intent,
            confidence=confidence,
            decision=decision,
            routed_agent=routed_agent,
        )
        db.add(db_obj)
        await db.flush()
        return db_obj
