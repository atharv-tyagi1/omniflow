"""Agent framework and implementations."""
from backend.app.agents.registry import AgentRegistry
from backend.app.agents.factory import AgentFactory
from backend.app.agents.base import BaseAgent

_registered = False


def _ensure_registered():
    """Explicitly register all agent implementations. Idempotent."""
    global _registered
    if _registered:
        return
    from backend.app.schemas.agent import AgentType

    # Register sales agent
    from backend.app.agents.sales import SalesAgent
    AgentRegistry.register(AgentType.SALES.value, SalesAgent)

    # Register support agent
    from backend.app.agents.support import SupportAgent
    AgentRegistry.register(AgentType.SUPPORT.value, SupportAgent)

    _registered = True


__all__ = ["AgentRegistry", "AgentFactory", "BaseAgent", "_ensure_registered"]
