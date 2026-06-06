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

from backend.app.services.router_service import RouterService
from backend.app.schemas.router import RouteMessageRequest, RouteMessageResponse
from backend.app.schemas.agent import AgentResponse
from backend.app.agents.factory import AgentFactory
from backend.app.agents.registry import AgentRegistry

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

    # ------------------------------------------------------------------
    # Phase 8: Agent orchestration entry point
    # ------------------------------------------------------------------
    @staticmethod
    async def handle_message(
        db: AsyncSession,
        workspace_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
        query: str,
    ) -> AgentResponse:
        """
        Orchestrates routing and agent execution.
        Decouples routing decisions from agent execution.
        """
        # Ensure agents are registered
        from backend.app.agents import _ensure_registered
        _ensure_registered()

        # Fetch conversation
        conversation = await db.get(Conversation, conversation_id)
        if not conversation:
            conversation = Conversation(
                id=conversation_id,
                workspace_id=workspace_id,
                customer_id=customer_id,
            )

        # 1. Routing
        request = RouteMessageRequest(conversation_id=conversation_id, message=query)
        decision_response: RouteMessageResponse = await RouterService.route_message(
            db=db,
            request=request,
            conversation=conversation,
            history=[],
        )

        # Determine the target agent type
        target_agent_type = (
            decision_response.routed_agent.value
            if decision_response.routed_agent
            else (
                decision_response.primary_intent.value
                if decision_response.primary_intent
                else "unknown"
            )
        )

        # Fallback if agent type is not registered
        if not AgentRegistry.is_registered(target_agent_type):
            logger.warning(
                f"Target agent {target_agent_type} is not registered. "
                "Falling back to generic/error response."
            )
            return AgentResponse(
                content=(
                    "I'm not quite sure how to help with that yet, or the specific "
                    "agent is offline. Let me connect you with someone who can."
                ),
                confidence=decision_response.confidence,
                agent_name="System",
                handoff_recommended=True,
                requires_human=True,
                sentiment="neutral",
            )

        # 2. Resolve Agent
        agent = AgentFactory.create_agent(target_agent_type)

        # 3. Execute Agent
        response = await agent.respond(
            db=db,
            conversation_id=conversation_id,
            customer_id=customer_id,
            workspace_id=workspace_id,
            query=query,
            router_metadata=decision_response.model_dump(),
        )

        return response
