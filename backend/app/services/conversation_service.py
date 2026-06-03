from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.core.exceptions import NotFoundError
from backend.app.core.agents.dispatcher import AgentDispatcher
from backend.app.core.ai.intent_router import IntentResult

logger = logging.getLogger(__name__)


class ConversationService:
    @staticmethod
    async def create_conversation(
        db: AsyncSession, workspace_id: UUID, customer_id: UUID, channel: str = "web"
    ) -> Conversation:
        return await ConversationRepository.create(
            db=db, workspace_id=workspace_id, customer_id=customer_id, channel=channel
        )

    @staticmethod
    async def get_conversation(
        db: AsyncSession, conversation_id: UUID, workspace_id: UUID
    ) -> Conversation:
        conversation = await ConversationRepository.get_by_id(
            db, conversation_id, workspace_id
        )
        if not conversation:
            raise NotFoundError("Conversation not found")
        return conversation

    @staticmethod
    async def list_conversations(
        db: AsyncSession, workspace_id: UUID
    ) -> List[Conversation]:
        return await ConversationRepository.list_by_workspace(db, workspace_id)

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
        sender_type: str,
        content: str,
    ) -> Message:
        # Verify conversation belongs to workspace
        await ConversationService.get_conversation(db, conversation_id, workspace_id)

        # 1. Persist the incoming message
        user_msg = await ConversationRepository.add_message(
            db=db,
            conversation_id=conversation_id,
            sender_type=sender_type,
            content=content,
        )

        # 2. If message is from a customer, trigger the AI agent pipeline
        if sender_type == "customer":
            try:
                # Fetch recent history for context
                history_msgs = (
                    await ConversationRepository.get_messages_by_conversation(
                        db, conversation_id
                    )
                )

                # Identify the previous agent, if any
                previous_agent = None
                for msg in reversed(history_msgs):
                    if msg.sender_type not in ["customer", "system"]:
                        previous_agent = msg.sender_type
                        break

                conversation_history = [m.content for m in history_msgs[-8:]]

                # Classify intent and dispatch to the correct agent
                intent, agent_response = await AgentDispatcher.dispatch(
                    message=content,
                    conversation_history=conversation_history,
                    db=db,
                    workspace_id=workspace_id,
                    previous_agent=previous_agent,
                )

                new_agent = agent_response.agent_type

                # Log handoff if the agent changed
                if previous_agent and previous_agent != new_agent:
                    from backend.app.repositories.handoff_repository import (
                        HandoffRepository,
                    )

                    await HandoffRepository.create(
                        db=db,
                        conversation_id=conversation_id,
                        from_agent=previous_agent,
                        to_agent=new_agent,
                        reason=f"Intent changed to {intent.primary_intent}",
                    )
                    logger.info(f"Handoff logged: {previous_agent} -> {new_agent}")

                # Persist the AI agent's reply using its specific agent type
                await ConversationRepository.add_message(
                    db=db,
                    conversation_id=conversation_id,
                    sender_type=new_agent,
                    content=agent_response.content,
                )

                logger.info(
                    f"Agent '{agent_response.agent_type}' responded to conversation "
                    f"{conversation_id} (intent={intent.primary_intent}, "
                    f"confidence={intent.confidence})"
                )
            except Exception as e:
                logger.error(
                    f"Agent pipeline failed for conversation {conversation_id}: {e}"
                )
                # Failure in the AI pipeline should never break the user's message persistence

        return user_msg

    @staticmethod
    async def classify_message(
        message: str, conversation_history: Optional[List[str]] = None
    ) -> IntentResult:
        """Standalone classification without generating a response — useful for analytics."""
        from backend.app.core.ai.intent_router import IntentRouter

        return await IntentRouter.classify(message, conversation_history)

    @staticmethod
    async def list_messages(
        db: AsyncSession, conversation_id: UUID, workspace_id: UUID
    ) -> List[Message]:
        # Verify ownership first
        await ConversationService.get_conversation(db, conversation_id, workspace_id)
        return await ConversationRepository.get_messages_by_conversation(
            db, conversation_id
        )
