"""Conversation Engine — DB-backed participant resolution, handoff tracking, and state updates."""

import logging
import uuid
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.conversation import Conversation
from backend.app.models.conversation_participant import ConversationParticipant

logger = logging.getLogger(__name__)


class ConversationEngine:
    """
    Handles:
    - Conversation ownership validation (workspace_id enforced)
    - Participant resolution (who is the active responder?)
    - Handoff state updates (agent → human, agent → agent)
    - Active participant tracking after each turn
    - Creating new conversation records
    """

    # ──────────────────────────────────────────────────────────────────────────
    # CONVERSATION MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────────

    async def get_or_create_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
        channel_id: Optional[UUID] = None,
    ) -> Conversation:
        """
        Retrieves an existing conversation or creates a new one.
        Validates workspace ownership on retrieval to prevent cross-tenant access.
        """
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.workspace_id == workspace_id,  # TENANT ISOLATION
            )
        )
        conv = result.scalars().first()

        if not conv:
            # Create new conversation
            conv = Conversation(
                id=conversation_id,
                workspace_id=workspace_id,
                channel_id=channel_id,
                status="active",
                handoff_status="none",
            )
            db.add(conv)
            await db.flush()
            logger.info(f"Created new conversation {conversation_id} for workspace {workspace_id}")

        return conv

    async def resolve_active_participant(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
    ) -> Optional[UUID]:
        """
        Determines the active participant (responder) for the conversation.
        Checks handoff state first, then active_participant_id.
        Returns the participant_id or None if unresolved.
        """
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.workspace_id == workspace_id,
            )
        )
        conv = result.scalars().first()

        if not conv:
            logger.warning(f"Conversation {conversation_id} not found for workspace {workspace_id}")
            return None

        # If a handoff is pending or complete, the human is the responder
        if conv.handoff_status in ("pending", "complete"):
            logger.debug(f"Conversation {conversation_id} is handed off to human")
            return conv.last_responding_participant_id

        return conv.active_participant_id

    # ──────────────────────────────────────────────────────────────────────────
    # PARTICIPANT TRACKING
    # ──────────────────────────────────────────────────────────────────────────

    async def register_agent_participant(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
        run_id: UUID,
    ) -> None:
        """Registers the agent run as a participant in the conversation."""
        try:
            # Check if already registered
            result = await db.execute(
                select(ConversationParticipant).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_id == run_id,
                )
            )
            existing = result.scalars().first()
            if existing:
                return

            participant = ConversationParticipant(
                conversation_id=conversation_id,
                workspace_id=workspace_id,
                participant_id=run_id,
                participant_type="agent",
            )
            db.add(participant)
            await db.flush()
            logger.debug(f"Registered agent run {run_id} as participant in {conversation_id}")
        except Exception as e:
            logger.warning(f"Failed to register participant: {e}")

    async def update_active_responder(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
        run_id: UUID,
    ) -> None:
        """
        Updates the active_participant_id and last_responding_participant_id
        after a successful turn.
        """
        try:
            await db.execute(
                update(Conversation)
                .where(
                    Conversation.id == conversation_id,
                    Conversation.workspace_id == workspace_id,
                )
                .values(
                    active_participant_id=run_id,
                    last_responding_participant_id=run_id,
                )
            )
            await db.flush()
        except Exception as e:
            logger.warning(f"Failed to update active responder for {conversation_id}: {e}")

    async def update_handoff_state(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
        current_run_id: UUID,
        target_type: str = "human",  # "human" or "agent"
    ) -> None:
        """
        Records an agent handoff — sets handoff_status to 'pending'.
        Used by the tool engine when a handoff action is triggered.
        """
        try:
            await db.execute(
                update(Conversation)
                .where(
                    Conversation.id == conversation_id,
                    Conversation.workspace_id == workspace_id,
                )
                .values(
                    handoff_status="pending",
                    last_responding_participant_id=current_run_id,
                )
            )
            await db.flush()
            logger.info(
                f"Handoff to {target_type} initiated for conversation {conversation_id} "
                f"from run {current_run_id}"
            )
        except Exception as e:
            logger.error(f"Failed to update handoff state for {conversation_id}: {e}")

    async def close_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
    ) -> None:
        """Marks a conversation as archived."""
        try:
            await db.execute(
                update(Conversation)
                .where(
                    Conversation.id == conversation_id,
                    Conversation.workspace_id == workspace_id,
                )
                .values(status="archived")
            )
            await db.flush()
        except Exception as e:
            logger.warning(f"Failed to close conversation {conversation_id}: {e}")
