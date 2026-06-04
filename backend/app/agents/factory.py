from typing import Optional
from backend.app.schemas.agent import AgentConfig
from backend.app.agents.base import BaseAgent
from backend.app.agents.registry import AgentRegistry

class AgentFactory:
    """Instantiates concrete agent instances based on registered types."""
    
    @staticmethod
    def create_agent(agent_type: str, config: Optional[AgentConfig] = None) -> BaseAgent:
        """
        Creates and returns an instance of the agent mapped to `agent_type`.
        Passes optional `config` overrides to the constructor.
        """
        agent_class = AgentRegistry.get_agent(agent_type)
        return agent_class(name=agent_type, config=config)
