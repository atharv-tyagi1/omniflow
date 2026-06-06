import logging
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.router_service import RouterService
from backend.app.schemas.router import RouterDecision, RouteMessageRequest, RouteMessageResponse
from backend.app.schemas.agent import AgentResponse, AgentType
from backend.app.agents.factory import AgentFactory
from backend.app.agents.registry import AgentRegistry
from backend.app.models.conversation import Conversation
# Ensure agents are registered
import backend.app.agents  # noqa

logger = logging.getLogger(__name__)

class ConversationService:
    """Orchestrates routing and agent execution."""

    @staticmethod
    async def handle_message(
        db: AsyncSession,
        workspace_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
        query: str,
    ) -> AgentResponse:
        """
        Main entry point for handling an incoming message.
        Decouples routing from execution.
        """
        # Fetch conversation
        conversation = await db.get(Conversation, conversation_id)
        if not conversation:
            # Create a dummy one for now if not found, or handle it
            conversation = Conversation(id=conversation_id, workspace_id=workspace_id, customer_id=customer_id)
            
        # 1. Routing
        request = RouteMessageRequest(conversation_id=conversation_id, message=query)
        decision_response: RouteMessageResponse = await RouterService.route_message(
            db=db,
            request=request,
            conversation=conversation,
            history=[]
        )
        
        # Determine the target agent type based on the router decision
        target_agent_type = decision_response.routed_agent.value if decision_response.routed_agent else decision_response.primary_intent.value if decision_response.primary_intent else "unknown"
        
        # If the specific agent is not yet implemented or registered, or it's unknown/clarify,
        # we might need a fallback. For now, if we mapped to sales, use sales.
        if not AgentRegistry.is_registered(target_agent_type):
            logger.warning(f"Target agent {target_agent_type} is not registered. Falling back to generic/error response.")
            return AgentResponse(
                content="I'm not quite sure how to help with that yet, or the specific agent is offline. Let me connect you with someone who can.",
                confidence=decision_response.confidence,
                agent_name="System",
                handoff_recommended=True,
                requires_human=True,
                sentiment="neutral"
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
            router_metadata=decision_response.model_dump()
        )
        
        return response
