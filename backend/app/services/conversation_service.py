from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from dataclasses import dataclass

@dataclass
class ConversationMessageResult:
    customer_message: Message
    agent_message: Optional[Message] = None

from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.core.exceptions import NotFoundError
from backend.app.core.agents.dispatcher import AgentDispatcher
from backend.app.core.ai.intent_router import IntentResult

from backend.app.services.router_service import RouterService
from backend.app.schemas.router import RouteMessageRequest, RouteMessageResponse, RouterDecision, AgentIntent
from backend.app.schemas.agent import AgentResponse
from backend.app.agents.factory import AgentFactory
from backend.app.agents.registry import AgentRegistry
from backend.app.core.config import settings
from backend.app.services.analytics.emitter import AnalyticsEventEmitter
from backend.app.schemas.analytics import AnalyticsEventType

logger = logging.getLogger(__name__)


class ConversationService:
    @staticmethod
    async def create_conversation(
        db: AsyncSession, workspace_id: UUID, customer_id: UUID, channel: str = "web"
    ) -> Conversation:
        return await ConversationRepository.create(
            db=db, workspace_id=workspace_id, customer_id=customer_id, channel=channel
        )
        # Note: conversation_started analytics event is emitted via handle_message
        # or backfill, not here, to avoid double-counting for pre-existing flows.

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
    async def get_active_by_customer(
        db: AsyncSession, customer_id: UUID, channel: str
    ) -> Optional[Conversation]:
        return await ConversationRepository.get_active_by_customer(db, customer_id, channel)

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
        sender_type: str,
        content: str,
    ) -> ConversationMessageResult:
        # Verify conversation belongs to workspace
        conversation = await ConversationService.get_conversation(db, conversation_id, workspace_id)

        # 1. Persist the incoming message
        user_msg = await ConversationRepository.add_message(
            db=db,
            conversation_id=conversation_id,
            sender_type=sender_type,
            content=content,
        )

        # Phase 12: Emit analytics event for messages (durable outbox)
        if sender_type == "customer":
            await AnalyticsEventEmitter.emit(
                db=db,
                workspace_id=workspace_id,
                event_type=AnalyticsEventType.MESSAGE_RECEIVED,
                conversation_id=conversation_id,
                metadata={"channel": "web"},
                idempotency_key=f"msg_received:{user_msg.id}",
            )

        agent_msg = None

        # 2. If message is from a customer, trigger the AI agent pipeline
        if sender_type == "customer":
            try:
                # Feature flag check for new Handoff architecture
                use_v2 = getattr(settings, "HANDOFF_V2_ENABLED", True)
                
                if use_v2:
                    # New Phase 11 Handoff V2 Flow
                    agent_response = await ConversationService.handle_message(
                        db=db,
                        workspace_id=workspace_id,
                        customer_id=conversation.customer_id,
                        conversation_id=conversation_id,
                        query=content,
                        source_message_id=str(user_msg.id)
                    )
                    
                    # Persist the AI agent's reply
                    agent_msg = await ConversationRepository.add_message(
                        db=db,
                        conversation_id=conversation_id,
                        sender_type=agent_response.agent_name or agent_response.agent_type,
                        content=agent_response.content,
                    )
                    return ConversationMessageResult(customer_message=user_msg, agent_message=agent_msg)
            except Exception as e:
                logger.error(
                    "Agent pipeline v2 failed for conversation %s",
                    conversation_id,
                    exc_info=False,
                    extra={
                        "event_type": "handoff_v2_fallback",
                        "failure_class": e.__class__.__name__,
                        "conversation_id": str(conversation_id),
                        "workspace_id": str(workspace_id),
                        "from_agent": conversation.current_agent or "system",
                        "target_agent": "v1_legacy",
                        "reason": "V2 Pipeline Exception",
                        "recoverable": True
                    }
                )
                # Continue and gracefully fallback to V1
                pass

            # V1 Legacy Flow
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
                agent_msg = await ConversationRepository.add_message(
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

        return ConversationMessageResult(customer_message=user_msg, agent_message=agent_msg)

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
        source_message_id: Optional[str] = None,
        lineage: Optional[dict] = None
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

        if decision_response.decision == RouterDecision.CLARIFY or decision_response.primary_intent == AgentIntent.UNKNOWN:
            return AgentResponse(
                content="I'm not quite sure how to help with that. Could you please clarify if you need sales, support, or customer care?",
                confidence=1.0,
                agent_name="system",
                handoff_recommended=True,
                requires_human=True,
                sentiment="neutral"
            )

        primary_intent = decision_response.primary_intent.value if decision_response.primary_intent else "unknown"

        # 2. Handoff Orchestration
        from backend.app.services.handoff.coordinator import HandoffCoordinator
        
        # Fetch recent history for context builder
        history_msgs = await ConversationRepository.get_messages_by_conversation(
            db, conversation_id
        )
        recent_messages = [m.content for m in history_msgs[-10:]]

        response = await HandoffCoordinator.handle_transition(
            db=db,
            conversation=conversation,
            primary_intent=primary_intent,
            query=query,
            recent_messages=recent_messages,
            router_metadata=decision_response.model_dump(),
            source_message_id=source_message_id,
            lineage=lineage
        )

        return response
