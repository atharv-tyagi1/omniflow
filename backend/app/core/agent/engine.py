from uuid import UUID
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import time

from backend.app.models.agent import Agent
from backend.app.models.agent_version import AgentVersion
from backend.app.core.ai.providers.registry import ProviderRegistry
from backend.app.core.agent.context_builder import ContextBuilder
from backend.app.core.agent.reasoning_layer import ReasoningLayer
from backend.app.core.agent.conversation_engine import ConversationEngine
from backend.app.core.agent.telemetry import TelemetryEngine
from backend.app.core.agent.exceptions import AgentRuntimeError, PolicyViolationError

class AgentRuntime:
    """
    The core runtime class responsible for the execution pipeline:
    Request -> Context -> Retrieval -> Tools -> LLM -> Persistence.
    Enforces explicit abuse guardrails.
    """

    MAX_TOOL_CALLS_PER_TURN = 5
    MAX_WORKFLOW_HOPS_PER_TURN = 3
    MAX_RETRY_BUDGET = 3

    def __init__(self, db: AsyncSession, agent: Agent, agent_version: AgentVersion):
        self.db = db
        self.agent = agent
        self.agent_version = agent_version
        
        # Track runtime budgets
        self._tool_calls_this_turn = 0
        self._workflow_hops_this_turn = 0
        self._policy_denials = 0

    async def execute_turn(
        self,
        workspace_id: UUID,
        conversation_id: UUID,
        user_query: str,
        workspace_policies: List[str] = None,
        available_tools: List[str] = None,
        available_workflows: List[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a single conversational turn for the agent.
        """
        run_id = uuid.uuid4()
        step_id = uuid.uuid4()
        start_time = time.time()

        try:
            # 1. Resolve participant and state
            active_agent_id = await ConversationEngine.resolve_active_participant(self.db, conversation_id)
            await ConversationEngine.track_responder(self.db, conversation_id, self.agent.id)

            # 2. Reasoning Layer
            model_id = ReasoningLayer.select_model(self.agent)

            # 3. Context Assembly
            context_string = await ContextBuilder.build_context(
                db=self.db,
                workspace_id=workspace_id,
                agent_id=self.agent.id,
                agent_version=self.agent_version,
                conversation_id=conversation_id,
                query=user_query,
                workspace_policies=workspace_policies or [],
                available_tools=available_tools or [],
                available_workflows=available_workflows or [],
                model_config={"model": model_id}
            )

            # 4. Provider Invocation
            provider = ProviderRegistry.get_provider("gemini")
            
            response = await provider.generate_completion(
                prompt=context_string,
                model=model_id
            )

            latency_ms = (time.time() - start_time) * 1000

            # 5. Telemetry
            await TelemetryEngine.log_decision_trace(
                db=self.db,
                workspace_id=workspace_id,
                agent_id=self.agent.id,
                run_id=run_id,
                step_id=step_id,
                provider="gemini",
                model=model_id,
                latency_ms=latency_ms,
                tokens_used=response.get("tokens_used", 0),
                tools_called=[], # In a real loop, track tools invoked
                context_metadata={"query_length": len(user_query)}
            )

            # Update state
            await ConversationEngine.update_participant_state(self.db, conversation_id, self.agent.id, "idle")

            return {
                "content": response.get("content", ""),
                "structured_data": response.get("structured_data"),
                "error": response.get("error")
            }
            
        except Exception as e:
            # Handle failure paths
            await ConversationEngine.update_participant_state(self.db, conversation_id, self.agent.id, "error")
            raise AgentRuntimeError(f"Agent turn failed: {str(e)}")

    def check_guardrails(self, is_workflow: bool = False):
        """
        Enforces execution budget limits to prevent infinite loops or abuse.
        """
        if self._policy_denials >= 3:
            raise PolicyViolationError("Agent aborted due to repeated policy denials.")

        if is_workflow:
            self._workflow_hops_this_turn += 1
            if self._workflow_hops_this_turn > self.MAX_WORKFLOW_HOPS_PER_TURN:
                raise PolicyViolationError("Maximum workflow hops per turn exceeded.")
        else:
            self._tool_calls_this_turn += 1
            if self._tool_calls_this_turn > self.MAX_TOOL_CALLS_PER_TURN:
                raise PolicyViolationError("Maximum tool calls per turn exceeded.")
