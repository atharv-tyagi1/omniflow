import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.ai.intent_router import IntentRouter, IntentResult
from backend.app.core.agents.base_agent import BaseAgent, AgentResponse
from backend.app.core.agents.sales_agent import SalesAgent
from backend.app.core.agents.support_agent import SupportAgent
from backend.app.core.agents.customer_care_agent import CustomerCareAgent

logger = logging.getLogger(__name__)

# Singleton agent instances — reusable across requests
_agents: dict[str, BaseAgent] = {
    "sales": SalesAgent(),
    "support": SupportAgent(),
    "customer_care": CustomerCareAgent(),
}


class AgentDispatcher:
    """
    Maps IntentRouter classification results to the correct agent and
    executes the response pipeline.

    Flow:
        Customer message → IntentRouter.classify() → AgentDispatcher.dispatch()
                         → KnowledgeService.search_knowledge() (if applicable)
                         → SelectedAgent.respond() → AgentResponse
    """

    @staticmethod
    async def dispatch(
        message: str,
        conversation_history: Optional[list[str]] = None,
        db: Optional[AsyncSession] = None,
        workspace_id: Optional[UUID] = None,
        previous_agent: Optional[str] = None
    ) -> tuple[IntentResult, AgentResponse]:
        """
        Full pipeline: classify the message, select an agent, fetch context, generate a response.
        """
        # 1. Classify via Router Agent
        intent = await IntentRouter.classify(message, conversation_history)
        logger.info(
            f"IntentRouter classified: primary={intent.primary_intent}, "
            f"secondary={intent.secondary_intent}, confidence={intent.confidence}"
        )

        # 2. Select agent — fall back to support if intent is unknown
        agent_key = intent.primary_intent if intent.primary_intent != "unknown" else "support"
        agent = _agents.get(agent_key, _agents["support"])

        # 3. Retrieve RAG Context (for Sales, Support, and Customer Care)
        context = {}
        if previous_agent and previous_agent != agent_key:
            context["system_note"] = f"SYSTEM NOTE: The customer was just transferred to you from the '{previous_agent}' team. Acknowledge this transition naturally and continue assisting them."
        if db and workspace_id and agent_key in ["sales", "support", "customer_care"]:
            from backend.app.services.knowledge_service import KnowledgeService
            try:
                search_results = await KnowledgeService.search_knowledge(
                    db=db,
                    workspace_id=workspace_id,
                    query=message,
                    limit=3
                )
                if search_results:
                    context["rag_chunks"] = [res["content"] for res in search_results]
            except Exception as e:
                logger.error(f"Failed to retrieve RAG context for agent {agent_key}: {e}")

        # 4. Generate response
        response = await agent.respond(
            message=message,
            conversation_history=conversation_history,
            context=context
        )

        # Attach routing metadata to the response
        if response.metadata is None:
            response.metadata = {}
        response.metadata["intent"] = intent.to_dict()

        return intent, response

