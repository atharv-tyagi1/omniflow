"""Agent framework and implementations."""
from backend.app.schemas.agent import AgentType
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.factory import AgentFactory
from backend.app.agents.base import BaseAgent
from backend.app.agents.sales import SalesAgent

# Auto-register agents
AgentRegistry.register(AgentType.SALES.value, SalesAgent)

__all__ = ["AgentRegistry", "AgentFactory", "BaseAgent", "SalesAgent"]
