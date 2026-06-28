import pytest
import uuid
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.agent.engine import AgentRuntime
from backend.app.models.agent import Agent
from backend.app.models.agent_version import AgentVersion
from backend.app.models.agent_run import AgentRun
from backend.app.models.agent_run_step import AgentRunStep
from backend.app.models.agent_decision_trace import AgentDecisionTrace
from backend.app.models.agent_log import AgentLog

@pytest.fixture
async def sample_workspace(db: AsyncSession):
    # This assumes workspace is created implicitly or there's a utility
    # We will just generate a workspace ID since the DB tables mostly cascade
    return uuid.uuid4()

@pytest.fixture
async def test_agent(db: AsyncSession, sample_workspace):
    agent_id = uuid.uuid4()
    agent = Agent(
        id=agent_id,
        workspace_id=sample_workspace,
        name="Test Agent",
        category="customer_support",
        is_public_allowed=True
    )
    db.add(agent)
    
    version_id = uuid.uuid4()
    version = AgentVersion(
        id=version_id,
        agent_id=agent_id,
        version_number=1,
        is_published=True
    )
    db.add(version)
    await db.commit()
    
    return agent, version

@pytest.mark.asyncio
async def test_agent_runtime_basic_execution(db: AsyncSession, test_agent, monkeypatch):
    agent, version = test_agent
    runtime = AgentRuntime()
    conversation_id = uuid.uuid4()
    
    agent_config = {
        "agent_name": agent.name,
        "category": agent.category,
        "system_prompt": "You are a helpful assistant.",
        "agent_prompt": "Answer briefly.",
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "temperature": 0.0,
        "tool_policies": [],
    }
    
    class MockProvider:
        async def generate_completion(self, *args, **kwargs):
            return {
                "content": "HELLO WORLD",
                "structured_data": None,
                "tool_calls": None,
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "finish_reason": "stop"
            }
            
    monkeypatch.setattr(
        "backend.app.core.agent.engine.provider_registry.get_provider",
        lambda x: MockProvider()
    )

    result = await runtime.execute(
        db=db,
        workspace_id=agent.workspace_id,
        agent_id=agent.id,
        version_id=version.id,
        conversation_id=conversation_id,
        user_message="Say exactly: HELLO WORLD",
        agent_config=agent_config,
        workspace_policies="Never use profanity.",
        is_public_allowed=agent.is_public_allowed
    )
    
    assert result["status"] == "success"
    assert "HELLO WORLD" in result["content"].upper()
    assert result["run_id"] is not None
    
    # Verify Telemetry
    run_query = await db.execute(select(AgentRun).where(AgentRun.id == uuid.UUID(result["run_id"])))
    run = run_query.scalar_one_or_none()
    assert run is not None
    assert run.status == "success"
    
    steps_query = await db.execute(select(AgentRunStep).where(AgentRunStep.run_id == run.id))
    steps = steps_query.scalars().all()
    assert len(steps) > 0
    assert any(s.step_type == "llm_call" for s in steps)
    
    trace_query = await db.execute(select(AgentDecisionTrace).where(AgentDecisionTrace.workspace_id == agent.workspace_id))
    traces = trace_query.scalars().all()
    assert len(traces) > 0
    
    log_query = await db.execute(select(AgentLog).where(AgentLog.run_id == run.id))
    logs = log_query.scalars().all()
    assert len(logs) > 0
    
    # Check that Workspace Policies were injected by checking the provider call manually or trusting the LLM obeyed

@pytest.mark.asyncio
async def test_agent_runtime_failure_injection_provider(db: AsyncSession, test_agent, monkeypatch):
    agent, version = test_agent
    runtime = AgentRuntime()
    conversation_id = uuid.uuid4()
    
    agent_config = {
        "agent_name": agent.name,
        "category": agent.category,
        "system_prompt": "You are a helpful assistant.",
        "agent_prompt": "Answer briefly.",
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "temperature": 0.0,
        "tool_policies": [],
    }
    
    class MockTimeoutProvider:
        async def generate_completion(self, *args, **kwargs):
            from backend.app.core.agent.exceptions import ProviderTimeoutError
            raise ProviderTimeoutError("Provider timeout simulated")
            
    monkeypatch.setattr(
        "backend.app.core.agent.engine.provider_registry.get_provider",
        lambda x: MockTimeoutProvider()
    )

    result = await runtime.execute(
        db=db,
        workspace_id=agent.workspace_id,
        agent_id=agent.id,
        version_id=version.id,
        conversation_id=conversation_id,
        user_message="Hello",
        agent_config=agent_config
    )
    
    assert result["status"] == "failed"
    assert "temporarily unavailable" in result["content"].lower()

@pytest.mark.asyncio
async def test_agent_runtime_graceful_memory_failure(db: AsyncSession, test_agent, monkeypatch):
    agent, version = test_agent
    runtime = AgentRuntime()
    conversation_id = uuid.uuid4()
    
    agent_config = {
        "agent_name": agent.name,
        "category": agent.category,
        "system_prompt": "You are a helpful assistant.",
        "agent_prompt": "Answer briefly.",
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "temperature": 0.0,
        "tool_policies": [],
    }
    
    class MockProvider:
        async def generate_completion(self, *args, **kwargs):
            return {
                "content": "HELLO WORLD",
                "structured_data": None,
                "tool_calls": None,
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "finish_reason": "stop"
            }
            
    monkeypatch.setattr(
        "backend.app.core.agent.engine.provider_registry.get_provider",
        lambda x: MockProvider()
    )
    
    # Mock MemoryEngine to crash
    async def crash_memory(*args, **kwargs):
        raise Exception("Database disconnected simulated crash")
        
    monkeypatch.setattr(runtime.memory_engine, "compile_memory_context", crash_memory)

    result = await runtime.execute(
        db=db,
        workspace_id=agent.workspace_id,
        agent_id=agent.id,
        version_id=version.id,
        conversation_id=conversation_id,
        user_message="Say exactly: HELLO WORLD",
        agent_config=agent_config
    )
    
    # Engine should STILL succeed and just bypass memory
    assert result["status"] == "success"
    assert result["memory_used"] is False

@pytest.mark.asyncio
async def test_agent_runtime_tool_denial_security(db: AsyncSession, test_agent, monkeypatch):
    """
    Test negative security: The LLM tries to call a tool it isn't allowed to call.
    """
    agent, version = test_agent
    runtime = AgentRuntime()
    conversation_id = uuid.uuid4()
    
    agent_config = {
        "agent_name": agent.name,
        "category": agent.category,
        "system_prompt": "You are a helpful assistant.",
        "agent_prompt": "Answer briefly.",
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "temperature": 0.0,
        "tool_policies": [],
    }
    
    class MockToolCallProvider:
        def __init__(self):
            self.calls = 0
            
        async def generate_completion(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return {
                    "content": "",
                    "structured_data": None,
                    "tool_calls": [{"id": "call_123", "function": {"name": "unauthorized_tool", "arguments": "{}"}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                    "finish_reason": "tool_calls"
                }
            return {
                "content": "I couldn't do that.",
                "structured_data": None,
                "tool_calls": None,
                "usage": {"prompt_tokens": 15, "completion_tokens": 5, "total_tokens": 20},
                "finish_reason": "stop"
            }
            
    monkeypatch.setattr(
        "backend.app.core.agent.engine.provider_registry.get_provider",
        lambda x: MockToolCallProvider()
    )

    result = await runtime.execute(
        db=db,
        workspace_id=agent.workspace_id,
        agent_id=agent.id,
        version_id=version.id,
        conversation_id=conversation_id,
        user_message="Do something bad",
        agent_config=agent_config
    )
    
    assert result["status"] == "success"
    # Tool call trace should show failure
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["tool"] == "unauthorized_tool"
    assert result["tool_calls"][0]["result_status"] == "error"

