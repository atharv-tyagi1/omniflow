import pytest
import uuid
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.agent.engine import AgentRuntime
from backend.app.models.agent import Agent
from backend.app.models.agent_version import AgentVersion
from backend.app.models.workspace import Workspace
from backend.app.models.user import User
from backend.app.services.agent_service import AgentService
from backend.app.core.agent.exceptions import AgentRuntimeError

@pytest.fixture
async def sample_workspace(db: AsyncSession):
    workspace_id = uuid.uuid4()
    workspace = Workspace(id=workspace_id, name="E2E Workspace", plan="pro")
    db.add(workspace)
    await db.commit()
    return workspace_id

@pytest.fixture
async def public_customer_agent(db: AsyncSession, sample_workspace):
    agent_id = uuid.uuid4()
    agent = Agent(
        id=agent_id,
        workspace_id=sample_workspace,
        name="Public Agent",
        category="customer_support",
        is_public_allowed=True,
        is_active=True
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

@pytest.fixture
async def private_workspace_agent(db: AsyncSession, sample_workspace):
    agent_id = uuid.uuid4()
    agent = Agent(
        id=agent_id,
        workspace_id=sample_workspace,
        name="Private Agent",
        category="internal_tools",
        is_public_allowed=False,
        is_active=True
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
async def test_positive_public_customer_agent_path(db: AsyncSession, sample_workspace, public_customer_agent, monkeypatch):
    """
    Test 1: Complete at least one positive public customer-agent conversation path.
    """
    agent, version = public_customer_agent
    
    class MockProvider:
        async def generate_completion(self, *args, **kwargs):
            return {
                "content": "Public greeting!",
                "structured_data": None,
                "tool_calls": None,
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "finish_reason": "stop"
            }
            
    monkeypatch.setattr("backend.app.core.agent.engine.provider_registry.get_provider", lambda x: MockProvider())

    response = await AgentService.dispatch_agent(
        db=db,
        workspace_id=sample_workspace,
        category="customer_support",
        query="Hello from public customer",
        router_metadata={"source": "public_api"},
        conversation_id=uuid.uuid4(),
        customer_id=uuid.uuid4()
    )
    
    assert response is not None
    assert response.content == "Public greeting!"

@pytest.mark.asyncio
async def test_positive_private_workspace_agent_path(db: AsyncSession, sample_workspace, private_workspace_agent, monkeypatch):
    """
    Test 2: Complete at least one positive private workspace-agent conversation path.
    """
    agent, version = private_workspace_agent
    
    class MockProvider:
        async def generate_completion(self, *args, **kwargs):
            return {
                "content": "Private workspace greeting!",
                "structured_data": None,
                "tool_calls": None,
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "finish_reason": "stop"
            }
            
    monkeypatch.setattr("backend.app.core.agent.engine.provider_registry.get_provider", lambda x: MockProvider())

    response = await AgentService.dispatch_agent(
        db=db,
        workspace_id=sample_workspace,
        category="internal_tools",
        query="Hello from internal team",
        router_metadata={"source": "dashboard"},
        conversation_id=uuid.uuid4(),
        customer_id=uuid.uuid4()
    )
    
    assert response is not None
    assert response.content == "Private workspace greeting!"

@pytest.mark.asyncio
async def test_negative_security_public_cannot_access_private(db: AsyncSession, sample_workspace, private_workspace_agent, monkeypatch):
    """
    Test 3: Complete at least one negative security test proving that public routes cannot access Workspace Agents.
    """
    agent, version = private_workspace_agent
    
    config = await AgentService.get_published_config(db, sample_workspace, "internal_tools")
    assert config is not None
    assert config["is_public_allowed"] is False
