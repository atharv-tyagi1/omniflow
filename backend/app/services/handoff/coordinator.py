import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from backend.app.models.conversation import Conversation
from backend.app.schemas.agent import AgentResponse
from backend.app.schemas.handoff import AgentType, HandoffReason

from backend.app.agents.factory import AgentFactory
from backend.app.services.handoff.rule_engine import HandoffRuleEngine
from backend.app.services.handoff.state_manager import HandoffStateManager
from backend.app.services.handoff.context_builder import HandoffContextBuilder
from backend.app.services.handoff.executor import HandoffExecutor
from backend.app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

class HandoffCoordinator:
    """
    Façade that orchestrates the handoff workflow using modular collaborators.
    """

    @staticmethod
    async def handle_transition(
        db: AsyncSession,
        conversation: Conversation,
        primary_intent: str,
        query: str,
        recent_messages: List[str],
        router_metadata: dict,
        source_message_id: Optional[str] = None,
        lineage: Optional[dict] = None
    ) -> AgentResponse:
        
        # 1. Extract State early so we can check idempotency properly
        state = HandoffStateManager.get_state(conversation)

        # 2. Idempotency Check with fingerprint fallback
        existing_handoff, generated_source_message_id = await HandoffStateManager.check_idempotency(
            db=db,
            workspace_id=conversation.workspace_id,
            conversation_id=conversation.id,
            source_message_id=source_message_id,
            query=query
        )
        # Use the generated fingerprint if one was created
        source_message_id = generated_source_message_id

        if existing_handoff:
            logger.info(f"Idempotency hit for query/message. Suppressing duplicate handoff.")
            # We skip evaluating a new handoff and just return the execution via active agent
            active_agent_name = conversation.current_agent or "support"
            return await AgentService.dispatch_agent(
                db=db,
                workspace_id=conversation.workspace_id,
                category=active_agent_name,
                query=query,
                router_metadata=router_metadata,
                conversation_id=conversation.id,
                customer_id=conversation.customer_id
            )

        # 3. Evaluate Rules
        active_agent = None
        if conversation.current_agent:
            try:
                active_agent = AgentType(conversation.current_agent)
            except ValueError:
                pass

        decision = HandoffRuleEngine.evaluate(
            active_agent=active_agent,
            primary_intent=primary_intent,
            cooldown_until=state.cooldown_until,
            previous_agent=state.previous_agent
        )

        if not decision.should_handoff:
            if decision.reason == HandoffReason.LOOP_PREVENTION:
                # Escalate to human or clarify
                logger.warning(
                    f"Loop prevention triggered for conversation {conversation.id}. Escalating.",
                    extra={
                        "event_type": "loop_prevention_triggered",
                        "workspace_id": str(conversation.workspace_id),
                        "conversation_id": str(conversation.id),
                        "from_agent": active_agent.value if active_agent else "system",
                        "to_agent": "human",
                        "reason": decision.reason.value,
                        "human_escalation_triggered": True
                    }
                )
                return AgentResponse(
                    content="It seems we are going in circles. I'm going to escalate this to a human specialist who can look into it directly.",
                    confidence=1.0,
                    agent_name=active_agent.value if active_agent else "system",
                    requires_human=True,
                    sentiment="frustrated"
                )
                
            # Continue with current agent (fallback to support if None)
            target_agent_name = active_agent.value if active_agent else "support"
            return await AgentService.dispatch_agent(
                db=db,
                workspace_id=conversation.workspace_id,
                category=target_agent_name,
                query=query,
                router_metadata=router_metadata,
                conversation_id=conversation.id,
                customer_id=conversation.customer_id
            )

        # 4. Build Context
        bounded_context = HandoffContextBuilder.build_transition_context(
            state=state,
            recent_messages=recent_messages,
            max_turns=5
        )

        # 5. Prepare state transition
        state.previous_agent = active_agent
        state.active_agent = decision.to_agent
        state.handoff_summary = decision.reason.value if decision.reason else "Standard transition"
        
        # Apply Cooldown (e.g., 5 minutes)
        if conversation.handoff_count and conversation.handoff_count >= 2:
            cooldown_dt = datetime.now(timezone.utc) + timedelta(minutes=5)
            state.cooldown_until = cooldown_dt.isoformat()
            state.cooldown_active = True
            conversation.loop_cooldown_until = cooldown_dt

        # Serialize State Manager
        HandoffStateManager.update_state(conversation, state)

        # 6. Execute Handoff (commits state implicitly via 2PC)
        return await HandoffExecutor.execute_handoff(
            db=db,
            conversation=conversation,
            decision=decision,
            source_message_id=source_message_id,
            query=query,
            router_metadata=router_metadata,
            bounded_context=bounded_context,
            lineage=lineage
        )
