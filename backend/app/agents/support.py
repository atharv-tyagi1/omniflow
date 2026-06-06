import time
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.base import BaseAgent
from backend.app.agents.context_builder import AgentContextBuilder
from backend.app.agents.prompt_builder import AgentPromptBuilder
from backend.app.schemas.agent import AgentConfig, AgentResponse, AgentMetrics, AgentContext
from backend.app.schemas.ai import AIRequest
from backend.app.services.ai_service import AIService
from backend.app.services.ticket_service import TicketService
from backend.app.schemas.support import SupportAgentOutput, ResolutionStatus

logger = logging.getLogger(__name__)

class SupportAgent(BaseAgent):
    def __init__(self, name: str = "SupportAgent", config: Optional[AgentConfig] = None):
        super().__init__(name=name, config=config)

    def get_instructions(self) -> str:
        return """You are the OmniFlow Support Agent. Your goal is to diagnose issues, provide step-by-step troubleshooting, and resolve technical or functional problems using the provided knowledge base (RAG).
Rules:
1. Diagnose the issue and classify its type (login, payment, setup, usage, bug, account, or unknown).
2. ONLY provide troubleshooting steps that are grounded in the provided documentation (RAG context). Do not invent steps.
3. Do not invent product capabilities or guess technical causes without evidence.
4. If the issue is not covered by documentation, or requires backend/system intervention, or is a persistent bug, set requires_human to True.
5. Do not attempt to sell upgrades, plans, or products. You are purely a technical support specialist.
6. Do not over-focus on emotional reassurance like a Customer Care bot. Be concise, technical, and solution-focused.
7. Ask clarifying questions if the issue is underspecified.
8. Explicitly confirm whether the issue is resolved before closing the conversation (setting resolution_status to resolved).
9. Output your response adhering to the SupportAgentOutput JSON schema.
"""

    async def respond(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        customer_id: UUID,
        workspace_id: UUID,
        query: str,
        router_metadata: dict
    ) -> AgentResponse:
        start_time = time.time()
        try:
            # 1. Load or Create Active Ticket
            ticket = await TicketService.get_or_create_ticket_for_conversation(
                db, workspace_id, customer_id, conversation_id
            )
            
            # 2. Build AgentContext
            context: AgentContext = await AgentContextBuilder.build_context(
                db=db,
                conversation_id=conversation_id,
                customer_id=customer_id,
                workspace_id=workspace_id,
                query=query,
                router_metadata=router_metadata,
            )
            
            # Inject Ticket Context
            ticket_context = (
                f"Current Ticket Status: {ticket.status}\n"
                f"Issue Type: {ticket.issue_type or 'Unknown'}\n"
                f"Probable Cause: {ticket.probable_cause or 'Unknown'}\n"
                f"Last Troubleshooting Step: {ticket.last_troubleshooting_step or 'None'}\n"
                f"Escalation Reason: {ticket.escalation_reason or 'None'}"
            )
            context.workspace_context["support_ticket_state"] = ticket_context

            # 3. Build Support Prompt
            system_prompt = AgentPromptBuilder.build_system_prompt(
                agent_name=self.name,
                base_instructions=self.get_instructions(),
                context=context,
            )
            
            history_text = AgentPromptBuilder.format_conversation_history(context.conversation_history)
            final_query = f"{history_text}\nUser: {query}".strip()

            # 4. Call AIService with Support structured output schema
            request = AIRequest(
                user_query=final_query,
                system_prompt=system_prompt,
                response_schema=SupportAgentOutput,
            )
            ai_response = await AIService.generate_response(request)

            if ai_response.error or not ai_response.structured_data:
                raise ValueError(f"AI Service failed to produce structured data: {ai_response.error}")

            # 5. Validate Result
            output = SupportAgentOutput(**ai_response.structured_data)
            
            # 6. Persist Ticket Updates
            troubleshooting_steps_text = "\n".join(output.troubleshooting_steps) if output.troubleshooting_steps else ticket.last_troubleshooting_step
            escalation_reason = None
            if output.requires_human or output.handoff_recommended:
                escalation_reason = "Agent escalated based on LLM decision (requires_human=True)."

            await TicketService.update_support_context(
                db,
                workspace_id=workspace_id,
                ticket_id=ticket.id,
                issue_type=output.issue_type.value,
                probable_cause=output.probable_cause or "",
                last_troubleshooting_step=troubleshooting_steps_text or "",
                status=output.resolution_status.value,
                escalation_reason=escalation_reason
            )

            # 7. Return Response Envelope
            agent_response = AgentResponse(
                content=output.customer_reply,
                confidence=output.confidence,
                agent_name=self.name,
                handoff_recommended=output.handoff_recommended or output.requires_human,
                requires_human=output.requires_human,
                next_agent=output.next_agent if output.handoff_recommended else None,
                sentiment="neutral",
                metadata={
                    "issue_type": output.issue_type.value,
                    "resolution_status": output.resolution_status.value,
                    "troubleshooting_steps": output.troubleshooting_steps,
                    "sources": output.sources,
                }
            )

            # Record metrics
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
