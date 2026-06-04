from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from backend.app.schemas.router import (
    AgentIntent,
    RouterDecision,
    RouteMessageRequest,
    RouteMessageResponse,
)
from backend.app.core.ai.intent_router import IntentRouter
from backend.app.models.conversation import Conversation
from backend.app.repositories.handoff_repository import HandoffRepository

class RouterService:
    CONFIDENCE_THRESHOLD = 0.70

    @staticmethod
    async def route_message(
        db: AsyncSession,
        request: RouteMessageRequest,
        conversation: Conversation,
        history: Optional[list[str]] = None
    ) -> RouteMessageResponse:
        # 1. Detect Intent using Phase 6 AI orchestration
        intent_result = await IntentRouter.classify(request.message, history)
        
        primary = intent_result.primary_intent
        secondary = intent_result.secondary_intent
        confidence = intent_result.confidence
        
        # 2. Read the active agent from the conversation state
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
        
        # 3. Apply Deterministic Routing Rules
        is_confident = confidence >= RouterService.CONFIDENCE_THRESHOLD

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
                decision = RouterDecision.CLARIFY
                route_reason = f"Low confidence ({confidence}) with no active agent."
                routed_agent = None
                if primary == AgentIntent.UNKNOWN:
                    decision = RouterDecision.UNKNOWN
                    
        # 4. Handoff Persistence & Conversation State Update
        if decision == RouterDecision.HANDOFF:
            from_agent = active_agent.value if active_agent else "system"
            to_agent = routed_agent.value
            
            # Update active agent
            await HandoffRepository.update_conversation_agent(db, conversation.id, to_agent)
            
            # Persist handoff
            await HandoffRepository.create(
                db=db,
                conversation_id=conversation.id,
                from_agent=from_agent,
                to_agent=to_agent,
                reason=route_reason,
                confidence=confidence
            )
            
        elif decision == RouterDecision.STAY and active_agent is None and routed_agent is not None:
            # First time setting an agent
            await HandoffRepository.update_conversation_agent(db, conversation.id, routed_agent.value)

        # 5. Build and Return standard Response
        return RouteMessageResponse(
            decision=decision,
            primary_intent=primary,
            secondary_intent=secondary,
            confidence=confidence,
            active_agent=active_agent,
            previous_agent=active_agent if not handoff_required else active_agent, # keeping it simple
            routed_agent=routed_agent,
            handoff_required=handoff_required,
            route_reason=route_reason
        )
