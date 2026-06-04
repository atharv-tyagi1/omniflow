import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from backend.app.schemas.router import (
    AgentIntent,
    RouterDecision,
    RouteMessageRequest,
    RouteMessageResponse,
    IntentResult,
)
from backend.app.core.ai.intent_router import IntentRouter
from backend.app.models.conversation import Conversation
from backend.app.repositories.handoff_repository import HandoffRepository
from backend.app.repositories.router_event_repository import RouterEventRepository
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class RouterService:

    @staticmethod
    async def route_message(
        db: AsyncSession,
        request: RouteMessageRequest,
        conversation: Conversation,
        history: Optional[list[str]] = None
    ) -> RouteMessageResponse:
        
        # 1. Detect Intent (with Fail-safe logic)
        try:
            intent_result = await IntentRouter.classify(request.message, history)
        except Exception as e:
            logger.error(f"Router AI failure: {e}")
            intent_result = IntentResult(
                primary_intent=AgentIntent.UNKNOWN,
                secondary_intent=None,
                confidence=0.0
            )
        
        primary = intent_result.primary_intent
        secondary = intent_result.secondary_intent
        confidence = intent_result.confidence
        
        # 2. Multi-Intent Priority Policy (customer_care > support > sales)
        PRIORITY = {
            AgentIntent.CUSTOMER_CARE: 3,
            AgentIntent.SUPPORT: 2,
            AgentIntent.SALES: 1,
            AgentIntent.UNKNOWN: 0,
        }
        
        if secondary and PRIORITY.get(secondary, 0) > PRIORITY.get(primary, 0):
            primary, secondary = secondary, primary
            logger.info(f"Router priority swap: Primary is now {primary}, Secondary is {secondary}")

        # 3. Read active agent from conversation
        active_agent = conversation.current_agent
        if active_agent:
            try:
                active_agent = AgentIntent(active_agent)
            except ValueError:
                active_agent = None
                
        decision = RouterDecision.UNKNOWN
        handoff_required = False
        routed_agent = None
        route_reason = "Evaluated via Smart Intent Router."
        
        # 4. Apply Deterministic Routing Rules with Configurable Threshold
        is_confident = confidence >= settings.ROUTER_CONFIDENCE_THRESHOLD

        if is_confident:
            if active_agent and primary == active_agent:
                decision = RouterDecision.STAY
                routed_agent = active_agent
                route_reason = f"High confidence ({confidence}) matches active agent."
            else:
                decision = RouterDecision.HANDOFF
                routed_agent = primary
                handoff_required = True
                route_reason = f"High confidence ({confidence}) requires routing to {primary}."
        else:
            if active_agent:
                decision = RouterDecision.STAY
                routed_agent = active_agent
                route_reason = f"Low confidence ({confidence}) detected, retaining active agent."
            else:
                # Failsafe: if classification fails or is low confidence with no agent
                decision = RouterDecision.CLARIFY
                route_reason = f"Low confidence ({confidence}) with no active agent."
                routed_agent = None
                
        # Handle the specific UNKNOWN intent fallback if confidence is low and it's ambiguous
        if not is_confident and primary == AgentIntent.UNKNOWN:
            decision = RouterDecision.CLARIFY

        # 5. Handoff Persistence & Conversation State Update
        if decision == RouterDecision.HANDOFF:
            from_agent = active_agent.value if active_agent else "system"
            to_agent = routed_agent.value
            
            await HandoffRepository.update_conversation_agent(db, conversation.id, to_agent)
            await HandoffRepository.create(
                db=db,
                conversation_id=conversation.id,
                from_agent=from_agent,
                to_agent=to_agent,
                reason=route_reason,
                confidence=confidence
            )
            
        elif decision == RouterDecision.STAY and active_agent is None and routed_agent is not None:
            await HandoffRepository.update_conversation_agent(db, conversation.id, routed_agent.value)

        # 6. Analytics Instrumentation: Persist to RouterEvent and log
        await RouterEventRepository.create(
            db=db,
            conversation_id=conversation.id,
            primary_intent=primary.value if primary else "unknown",
            secondary_intent=secondary.value if secondary else None,
            confidence=confidence,
            decision=decision.value,
            routed_agent=routed_agent.value if routed_agent else None,
        )
        
        logger.info(
            "Router Decision Executed",
            extra={
                "primary_intent": primary.value if primary else "unknown",
                "secondary_intent": secondary.value if secondary else None,
                "confidence": confidence,
                "decision": decision.value,
                "routed_agent": routed_agent.value if routed_agent else None,
            }
        )

        return RouteMessageResponse(
            decision=decision,
            primary_intent=primary,
            secondary_intent=secondary,
            confidence=confidence,
            active_agent=active_agent,
            previous_agent=active_agent if not handoff_required else active_agent, 
            routed_agent=routed_agent,
            handoff_required=handoff_required,
            route_reason=route_reason
        )
