import time
import logging
from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.schemas.agent import (
    AgentConfig,
    AgentResponse,
    AgentContext,
    AgentMetrics,
)
from backend.app.schemas.ai import AIRequest
from backend.app.services.ai_service import AIService
from backend.app.agents.context_builder import AgentContextBuilder
from backend.app.agents.prompt_builder import AgentPromptBuilder

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract Base Class for all OmniFlow AI Agents.
    Forces standard interfaces for system prompts, execution, and fail-safes.
    """

    def __init__(self, name: str, config: Optional[AgentConfig] = None):
        self.name = name
        self.config = config or AgentConfig()

    @abstractmethod
    def get_instructions(self) -> str:
        """Returns the core behavioral instructions specific to this agent."""
        pass

    def handle_error(self, e: Exception) -> AgentResponse:
        """Fallback response generator during critical failures."""
        logger.error(f"Agent {self.name} encountered an error: {e}", exc_info=True)
        return AgentResponse(
            content="I'm currently experiencing technical difficulties. Please hold while I connect you with a human agent.",
            confidence=0.0,
            agent_name=self.name,
            handoff_recommended=True,
            requires_human=True,
            sentiment="neutral",
        )

    async def respond(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        customer_id: UUID,
        workspace_id: UUID,
        query: str,
        router_metadata: dict
    ) -> AgentResponse:
        """Orchestrates context, prompt, AI execution, and observability tracking."""
        start_time = time.time()
        
        try:
            # 1. Build Context
            context: AgentContext = await AgentContextBuilder.build_context(
                db=db,
                conversation_id=conversation_id,
                customer_id=customer_id,
                workspace_id=workspace_id,
                query=query,
                router_metadata=router_metadata,
            )

            # 2. Build System Prompt
            system_prompt = AgentPromptBuilder.build_system_prompt(
                agent_name=self.name,
                base_instructions=self.get_instructions(),
                context=context,
            )
            
            # Combine history and current query
            history_text = AgentPromptBuilder.format_conversation_history(context.conversation_history)
            final_query = f"{history_text}\nUser: {query}".strip()

            # 3. Prepare AI Request
            request = AIRequest(
                user_query=final_query,
                system_prompt=system_prompt,
                response_schema=AgentResponse,
            )

            # 4. Execute Generation
            ai_response = await AIService.generate_response(request)

            if ai_response.error or not ai_response.structured_data:
                raise ValueError(f"AI Service failed to produce structured data: {ai_response.error}")

            # 5. Parse and Validate Response
            agent_response = AgentResponse(**ai_response.structured_data)
            
            # Ensure agent name is injected properly if missing
            if not agent_response.agent_name or agent_response.agent_name.lower() == "unknown":
                agent_response.agent_name = self.name

            # 6. Record Observability Metrics
            latency = int((time.time() - start_time) * 1000)
            metrics = AgentMetrics(
                agent_name=self.name,
                latency_ms=latency,
                token_usage=ai_response.tokens_used or 0,
                confidence=agent_response.confidence,
                handoff_recommended=agent_response.handoff_recommended,
            )
            logger.info(f"Agent Execution Metrics: {metrics.model_dump()}")

            return agent_response

        except Exception as e:
            return self.handle_error(e)
