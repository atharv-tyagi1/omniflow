from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class AgentResponse:
    """Standardized response from any agent."""
    content: str
    agent_type: str
    metadata: Optional[dict] = None


class BaseAgent(ABC):
    """
    Abstract base class for all OmniFlow agents.

    Only four agents are approved (Master Build Instructions §AGENT RULES):
    - Sales Agent
    - Support Agent
    - Customer Care Agent
    - Router Agent (implemented separately as IntentRouter)

    All agents share a common async interface. Business logic lives exclusively
    inside these agent classes — never in controllers, routes, or repositories.
    """

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Identifier string for this agent (e.g. 'sales', 'support')."""
        ...

    @abstractmethod
    async def respond(
        self,
        message: str,
        conversation_history: Optional[list[str]] = None,
        context: Optional[dict] = None
    ) -> AgentResponse:
        """
        Generate a response to the customer's message.

        Args:
            message: The raw customer message.
            conversation_history: Ordered list of prior turns for contextual grounding.
            context: Optional workspace-specific context (e.g. RAG chunks, product catalog).

        Returns:
            AgentResponse with the generated content and agent metadata.
        """
        ...
