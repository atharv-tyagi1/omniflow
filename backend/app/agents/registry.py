from typing import Type
from backend.app.schemas.agent import AgentType
from backend.app.agents.base import BaseAgent

class AgentRegistry:
    """Central registry mapping AgentTypes to concrete Agent classes."""
    _registry: dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """Registers a concrete agent class for a specific agent type."""
        cls._registry[agent_type] = agent_class

    @classmethod
    def get_agent(cls, agent_type: str) -> Type[BaseAgent]:
        """Retrieves the concrete agent class for the given type."""
        agent_class = cls._registry.get(agent_type)
        if not agent_class:
            raise ValueError(f"No agent registered for type: {agent_type}")
        return agent_class
        
    @classmethod
    def list_agents(cls) -> list[str]:
        """Returns a list of all currently registered agent types."""
        return list(cls._registry.keys())
        
    @classmethod
    def is_registered(cls, agent_type: str) -> bool:
        """Checks if a specific agent type is registered."""
        return agent_type in cls._registry
