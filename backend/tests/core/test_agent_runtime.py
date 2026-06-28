import pytest
import asyncio
from backend.app.core.agent.engine import AgentRuntime
from backend.app.core.agent.context_builder import ContextBuilder
from backend.app.core.agent.telemetry import TelemetryEngine
from backend.app.core.agent.exceptions import MaxRecursionError

@pytest.mark.asyncio
async def test_context_builder_workspace_policies():
    """Verify that workspace policies are strictly placed at the top of the context."""
    builder = ContextBuilder()
    messages = await builder.build_messages(
        system_prompt="You are a helpful agent.",
        agent_prompt="Answer questions.",
        workspace_policies="NO PROFANITY. DO NOT SHARE SECRETS.",
        conversation_history=[{"role": "user", "content": "Hello"}]
    )
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "NO PROFANITY" in messages[0]["content"]
    assert "[WORKSPACE POLICIES - STRICTLY ENFORCED]" in messages[0]["content"]

@pytest.mark.asyncio
async def test_telemetry_redaction():
    """Verify that sensitive information is redacted from telemetry metadata."""
    telemetry = TelemetryEngine()
    metadata = {
        "model": "gemini-2.0-flash",
        "api_key": "sk-1234567890",
        "password": "supersecretpass",
        "reasoning": "I should steal the user data"
    }
    
    safe_data = telemetry._redact_sensitive_data(metadata)
    assert safe_data["model"] == "gemini-2.0-flash"
    assert safe_data["api_key"] == "***REDACTED***"
    assert safe_data["password"] == "***REDACTED***"
    assert safe_data["reasoning"] == "***REDACTED_FOR_PRIVACY***"

@pytest.mark.asyncio
async def test_agent_runtime_max_recursion_guardrail():
    """Verify that the engine strictly enforces tool call limits."""
    runtime = AgentRuntime()
    # Stub the MAX_TOOL_CALLS for quicker testing
    runtime.MAX_TOOL_CALLS_PER_TURN = 2
    
    class MaliciousProvider:
        async def generate_completion(self, **kwargs):
            # Always return a tool call to simulate infinite recursion
            return {
                "content": "",
                "tool_calls": [{"name": "some_tool"}],
                "usage": {"total_tokens": 10}
            }
            
    # Swap provider in test
    from backend.app.core.ai.providers.registry import provider_registry
    provider_registry.register("malicious", MaliciousProvider())
    
    # We expect this to fail due to MaxRecursionError but wrapped in AgentRuntimeError
    from backend.app.core.agent.exceptions import AgentRuntimeError
    
    with pytest.raises(AgentRuntimeError) as exc:
        await runtime.execute_turn(
            conversation_id="conv_1",
            agent_config={"agent_id": "test", "provider": "malicious"},
            user_message="Go infinite",
            conversation_history=[],
            workspace_policies=""
        )
        
    assert "Maximum tool calls per turn exceeded" in str(exc.value)

@pytest.mark.asyncio
async def test_agent_runtime_successful_turn():
    """Verify a successful execution path with telemetry."""
    runtime = AgentRuntime()
    
    class MockProvider:
        async def generate_completion(self, **kwargs):
            return {
                "content": "Hello, world!",
                "tool_calls": None,
                "usage": {"total_tokens": 15}
            }
            
    from backend.app.core.ai.providers.registry import provider_registry
    provider_registry.register("mock", MockProvider())
    
    result = await runtime.execute_turn(
        conversation_id="conv_2",
        agent_config={"agent_id": "test_agent", "provider": "mock"},
        user_message="Say hello",
        conversation_history=[],
        workspace_policies="Be polite."
    )
    
    assert result["status"] == "success"
    assert result["content"] == "Hello, world!"
