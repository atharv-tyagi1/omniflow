import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from backend.app.schemas.agent import AgentConfig, AgentResponse, AgentContext, AgentType
from backend.app.schemas.ai import AIResponse
from backend.app.agents.base import BaseAgent
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.factory import AgentFactory
from backend.app.agents.context_builder import AgentContextBuilder
from backend.app.agents.prompt_builder import AgentPromptBuilder


# ---------------------------------------------------------------------------
# Dummy implementations for testing
# ---------------------------------------------------------------------------
class DummyAgent(BaseAgent):
    def get_instructions(self) -> str:
        return "I am a dummy agent used for testing."


# ---------------------------------------------------------------------------
# Tests: Context Builder
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_agent_context_builder():
    db = AsyncMock()
    conv_id = uuid4()
    cust_id = uuid4()
    work_id = uuid4()
    
    context = await AgentContextBuilder.build_context(
        db=db,
        conversation_id=conv_id,
        customer_id=cust_id,
        workspace_id=work_id,
        query="Hello",
        router_metadata={"confidence": 0.9}
    )
    
    assert isinstance(context, AgentContext)
    assert context.workspace_context["id"] == str(work_id)
    assert context.customer_context["id"] == str(cust_id)
    assert context.router_metadata["confidence"] == 0.9


# ---------------------------------------------------------------------------
# Tests: Prompt Builder
# ---------------------------------------------------------------------------
def test_agent_prompt_builder():
    context = AgentContext(
        conversation_history=[{"role": "user", "content": "Hi"}],
        rag_context=["Policy A"],
        workspace_context={"name": "Test"},
        customer_context={"tier": "Pro"},
        conversation_state={"status": "open"}
    )
    
    prompt = AgentPromptBuilder.build_system_prompt("TestAgent", "Be helpful.", context)
    
    assert "You are the TestAgent for OmniFlow." in prompt
    assert "Be helpful." in prompt
    assert "Workspace Settings: {'name': 'Test'}" in prompt
    assert "Customer Profile: {'tier': 'Pro'}" in prompt
    assert "- Policy A" in prompt
    assert "Conversation State: {'status': 'open'}" in prompt
    assert "SCHEMA REQUIREMENTS" in prompt


def test_agent_prompt_builder_format_history():
    history = [{"role": "user", "content": "A"}, {"role": "agent", "content": "B"}]
    formatted = AgentPromptBuilder.format_conversation_history(history)
    assert "user: A\nagent: B" in formatted


# ---------------------------------------------------------------------------
# Tests: Registry and Factory
# ---------------------------------------------------------------------------
def test_agent_registry_and_factory():
    # Registration
    AgentRegistry.register("dummy", DummyAgent)
    assert "dummy" in AgentRegistry.list_agents()
    assert AgentRegistry.is_registered("dummy") is True
    assert AgentRegistry.is_registered("unknown_agent") is False
    
    # Factory instantiation
    agent = AgentFactory.create_agent("dummy", AgentConfig(temperature=0.5))
    assert isinstance(agent, DummyAgent)
    assert agent.name == "dummy"
    assert agent.config.temperature == 0.5
    
    # Factory failure
    with pytest.raises(ValueError):
        AgentFactory.create_agent("unknown_agent")


# ---------------------------------------------------------------------------
# Tests: BaseAgent Execution and Error Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_base_agent_respond_success():
    agent = DummyAgent(name="dummy")
    db = AsyncMock()
    
    with patch("backend.app.agents.base.AIService.generate_response", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(
            content="{}",
            structured_data={
                "content": "Success response",
                "confidence": 0.99,
                "agent_name": "dummy",
                "handoff_recommended": False,
                "sentiment": "happy",
                "requires_human": False
            },
            tokens_used=42
        )
        
        response = await agent.respond(db, uuid4(), uuid4(), uuid4(), "Test", {})
        
        assert isinstance(response, AgentResponse)
        assert response.content == "Success response"
        assert response.confidence == 0.99
        assert response.agent_name == "dummy"


@pytest.mark.asyncio
async def test_base_agent_respond_failure_triggers_safeguard():
    agent = DummyAgent(name="dummy")
    db = AsyncMock()
    
    with patch("backend.app.agents.base.AIService.generate_response", new_callable=AsyncMock) as mock_ai:
        # Simulate AI raising an exception (e.g., Timeout)
        mock_ai.side_effect = Exception("AI Provider Timeout")
        
        response = await agent.respond(db, uuid4(), uuid4(), uuid4(), "Test", {})
        
        # Ensure fallback safeguard triggered
        assert isinstance(response, AgentResponse)
        assert response.confidence == 0.0
        assert response.handoff_recommended is True
        assert response.requires_human is True
        assert "technical difficulties" in response.content

