import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from backend.app.models.handoff import Handoff
from backend.app.models.conversation import Conversation
from backend.app.schemas.handoff import ConversationHandoffStateV1, AgentType

logger = logging.getLogger(__name__)

class HandoffStateManager:
    """
    Manages the versioned JSONB state and idempotency checks.
    """

    @staticmethod
    async def check_idempotency(
        db: AsyncSession,
        workspace_id: UUID,
        conversation_id: UUID,
        source_message_id: Optional[str] = None,
        query: Optional[str] = None,
        source_channel: str = "web"
    ) -> Tuple[Optional[Handoff], Optional[str]]:
        """
        Returns existing completed handoff if source_message_id was already processed.
        If source_message_id is missing, falls back to an HMAC fingerprint of the inbound context.
        """
        if not source_message_id and query:
            import hmac
            import hashlib
            from backend.app.core.config import settings
            
            secret = getattr(settings, "SECRET_KEY", "fallback_dev_secret").encode()
            normalized_query = query.strip().lower()
            fingerprint_base = f"{workspace_id}:{conversation_id}:{source_channel}:{normalized_query}"
            
            # Prefix with 'hmac_' so it's distinguishable from a real message ID
            source_message_id = "hmac_" + hmac.new(
                secret,
                fingerprint_base.encode(),
                hashlib.sha256
            ).hexdigest()
            
        if not source_message_id:
            return None, None
            
        stmt = select(Handoff).where(
            Handoff.workspace_id == workspace_id,
            Handoff.conversation_id == conversation_id,
            Handoff.source_message_id == source_message_id,
            Handoff.status == "completed"
        ).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none(), source_message_id

    @staticmethod
    def get_state(conversation: Conversation) -> ConversationHandoffStateV1:
        """
        Extracts bounded versioned state from Conversation.
        """
        version = getattr(conversation, 'current_state_version', 1) or 1
        if version != 1:
            logger.warning(f"Unsupported state version {version}. Falling back to default empty state.")
            state_data = {}
        else:
            state_data = conversation.current_state or {}
            
        try:
            state = ConversationHandoffStateV1(**state_data)
        except Exception as e:
            logger.warning(f"Failed to parse ConversationHandoffStateV1: {e}")
            state = ConversationHandoffStateV1()
            
        # Ensure active_agent matches DB column if possible
        if conversation.current_agent and not state.active_agent:
            try:
                state.active_agent = AgentType(conversation.current_agent)
            except ValueError:
                pass
                
        return state

    @staticmethod
    def update_state(conversation: Conversation, state: ConversationHandoffStateV1) -> None:
        """
        Serializes and sets the bounded state on the Conversation.
        """
        conversation.current_state = state.model_dump(exclude_none=True)
        conversation.current_state_version = 1
