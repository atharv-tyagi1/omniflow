import time
import logging
from typing import Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.base import BaseAgent
from backend.app.agents.context_builder import AgentContextBuilder
from backend.app.agents.prompt_builder import AgentPromptBuilder
from backend.app.schemas.agent import AgentConfig, AgentResponse, AgentMetrics, AgentContext
from backend.app.schemas.ai import AIRequest
from backend.app.services.ai_service import AIService
from backend.app.services.customer_care_service import CustomerCareService
from backend.app.schemas.customer_care import CustomerCareAgentOutput, CustomerCareStage

logger = logging.getLogger(__name__)

class CustomerCareAgent(BaseAgent):
    def __init__(self, name: str = "CustomerCareAgent", config: Optional[AgentConfig] = None):
        super().__init__(name=name, config=config)

    def get_instructions(self) -> str:
        return """You are the OmniFlow Customer Care Agent, a highly empathetic retention and resolution specialist.
Your goal is to handle post-purchase complaints, refund requests, order/account issues, and dissatisfaction while preserving customer trust.

Rules:
1. Always acknowledge frustration and validate the customer's feelings before attempting a resolution.
2. Be calm, respectful, and use the highest empathy level of any agent.
3. Handle complaints, refunds, and order/account issues using the provided context.
4. Do NOT guess order/account outcomes without data. Provide clear timelines if resolution is not immediate.
5. Do NOT invent refund policies, compensation, or unsupported promises.
6. Do NOT attempt to sell upgrades, plans, or products (you are not a sales bot).
7. Do NOT over-focus on technical troubleshooting (you are not a technical support bot).
8. Do NOT override the router's intent decisions.
9. Set requires_human to True if: the refund policy is unclear, compensation is requested, chargeback or legal language appears, manual account/order intervention is needed, repeated dissatisfaction is detected, or the customer explicitly requests a human.
10. Output your response adhering to the CustomerCareAgentOutput JSON schema.
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
            # 1. Load or Create Active Customer Care Case
            care_case = await CustomerCareService.get_or_create_case_for_conversation(
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
            
            # Inject Customer Care Context
            case_context = (
                f"Current Case Stage: {care_case.current_stage}\n"
                f"Complaint Type: {care_case.complaint_type or 'Unknown'}\n"
                f"Refund Requested: {care_case.refund_requested}\n"
                f"Refund Amount: {care_case.refund_amount_requested or 'None'}\n"
                f"Order ID: {care_case.order_id or 'None'}\n"
                f"Account Issue Type: {care_case.account_issue_type or 'None'}\n"
                f"Sentiment: {care_case.sentiment or 'Unknown'}\n"
                f"Resolution Timeline: {care_case.resolution_timeline or 'None'}\n"
                f"Escalation Reason: {care_case.escalation_reason or 'None'}"
            )
            context.workspace_context["customer_care_case_state"] = case_context

            # 3. Build Support Prompt
            system_prompt = AgentPromptBuilder.build_system_prompt(
                agent_name=self.name,
                base_instructions=self.get_instructions(),
                context=context,
            )
            
            history_text = AgentPromptBuilder.format_conversation_history(context.conversation_history)
            final_query = f"{history_text}\nUser: {query}".strip()

            # 4. Call AIService with CustomerCare structured output schema
            request = AIRequest(
                user_query=final_query,
                system_prompt=system_prompt,
                response_schema=CustomerCareAgentOutput,
            )
            ai_response = await AIService.generate_response(request)

            if ai_response.error or not ai_response.structured_data:
                raise ValueError(f"AI Service failed to produce structured data: {ai_response.error}")

            # 5. Validate Result
            output = CustomerCareAgentOutput(**ai_response.structured_data)
            
            # 6. Persist Case Updates
            escalation_reason = None
            if output.requires_human or output.handoff_recommended:
                escalation_reason = "Agent escalated based on LLM decision (requires_human=True)."

            # Convert refund_amount_requested to Decimal if present
            refund_amount = None
            if output.refund_amount_requested is not None:
                refund_amount = Decimal(str(output.refund_amount_requested))

            await CustomerCareService.update_case_context(
                db,
                workspace_id=workspace_id,
                case_id=care_case.id,
                complaint_type=output.complaint_type.value,
                refund_requested=output.refund_requested,
                refund_amount_requested=refund_amount,
                order_id=output.order_id,
                account_issue_type=output.account_issue_type,
                sentiment=output.sentiment.value,
                current_stage=output.resolution_status.value,
                resolution_timeline=output.resolution_timeline,
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
                sentiment=output.sentiment.value,
                metadata={
                    "complaint_type": output.complaint_type.value,
                    "resolution_status": output.resolution_status.value,
                    "refund_requested": output.refund_requested,
                    "resolution_timeline": output.resolution_timeline,
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
