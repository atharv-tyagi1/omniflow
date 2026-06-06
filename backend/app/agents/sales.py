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
from backend.app.services.lead_profile_service import LeadProfileService
from backend.app.schemas.sales import SalesAgentOutput, LeadQualification, SalesFunnelStage

logger = logging.getLogger(__name__)

class SalesAgent(BaseAgent):
    def __init__(self, name: str = "SalesAgent", config: Optional[AgentConfig] = None):
        super().__init__(name=name, config=config)

    def get_instructions(self) -> str:
        return """You are the OmniFlow Sales Agent. Your goal is to guide the user through the sales funnel.
Rules:
1. Qualify the lead by gently extracting their budget, urgency, company size, and primary use case.
2. Handle objections professionally.
3. If the user asks for pricing details that depend on enterprise scale, or requests custom pricing, DO NOT invent numbers. You must set requires_human to True.
4. If the user mentions legal, compliance, or unsupported requests, set requires_human to True.
5. If you successfully answer objections and the customer is ready to buy, update the stage to ready_to_buy.
6. Provide a concise, helpful response to the user in the customer_reply field.
7. Return your internal assessments in the respective fields of the structured output schema.
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
            # 1. Load LeadProfile
            lead_profile = await LeadProfileService.get_lead(db, workspace_id, customer_id)
            
            # 2. Build AgentContext
            context: AgentContext = await AgentContextBuilder.build_context(
                db=db,
                conversation_id=conversation_id,
                customer_id=customer_id,
                workspace_id=workspace_id,
                query=query,
                router_metadata=router_metadata,
            )
            
            # Inject LeadProfile into context
            lead_context = "No existing lead profile."
            if lead_profile:
                lead_context = (
                    f"Current Stage: {lead_profile.current_stage.value}\n"
                    f"Buying Intent: {lead_profile.buying_intent.value if lead_profile.buying_intent else 'Unknown'}\n"
                    f"Known Budget: {lead_profile.budget or 'Unknown'}\n"
                    f"Past Objections: {', '.join(lead_profile.objections) if lead_profile.objections else 'None'}"
                )
            context.workspace_context["lead_profile_state"] = lead_context

            # 3. Build Sales Prompt
            system_prompt = AgentPromptBuilder.build_system_prompt(
                agent_name=self.name,
                base_instructions=self.get_instructions(),
                context=context,
            )
            
            history_text = AgentPromptBuilder.format_conversation_history(context.conversation_history)
            final_query = f"{history_text}\nUser: {query}".strip()

            # 4. Call AIService with Sales structured output schema
            request = AIRequest(
                user_query=final_query,
                system_prompt=system_prompt,
                response_schema=SalesAgentOutput,
            )
            ai_response = await AIService.generate_response(request)

            if ai_response.error or not ai_response.structured_data:
                raise ValueError(f"AI Service failed to produce structured data: {ai_response.error}")

            # 5. Validate Result
            output = SalesAgentOutput(**ai_response.structured_data)
            
            # 6. Persist LeadProfile Changes
            # Extract qualification
            qual = LeadQualification(
                budget=output.budget,
                urgency=output.urgency,
                company_size=output.company_size,
                use_case=output.use_case,
                buying_intent=output.buying_intent
            )
            
            # Update Lead qualification & intent
            # Note: process_qualification also acts as an upsert, creating the lead if missing
            lead = await LeadProfileService.process_qualification(db, workspace_id, customer_id, qual)
            
            if output.current_stage and output.current_stage != lead.current_stage:
                try:
                    await LeadProfileService.move_to_stage(db, workspace_id, customer_id, output.current_stage)
                except ValueError as e:
                    logger.warning(f"SalesAgent proposed invalid stage transition: {e}")
                    
            if output.objections:
                for obj in output.objections:
                    if obj not in lead.objections:
                        await LeadProfileService.log_objection(db, workspace_id, customer_id, obj)

            # 7. Return Response Envelope
            agent_response = AgentResponse(
                content=output.customer_reply,
                confidence=1.0,  # Or calculate based on lead_score if applicable, defaulting to high for now
                agent_name=self.name,
                handoff_recommended=output.handoff_recommended or output.requires_human,
                requires_human=output.requires_human,
                next_agent=output.next_agent if output.handoff_recommended else None,
                sentiment="neutral",
                metadata={
                    "lead_score": output.lead_score,
                    "next_best_action": output.next_best_action
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
