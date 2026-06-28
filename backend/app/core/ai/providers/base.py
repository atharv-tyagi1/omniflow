"""Base Provider Abstraction Layer for OmniFlow LLM interactions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseProvider(ABC):
    """Abstract base class for all AI LLM providers in the OmniFlow platform.
    
    This enforces a strict abstraction layer to guarantee that the core
    AgentRuntime is completely agnostic to the underlying LLM provider.
    """

    @abstractmethod
    async def generate_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a chat completion from the provider.
        
        Args:
            messages: List of message dicts (e.g., {"role": "user", "content": "..."})
            model: The specific model ID to use (e.g., "gemini-1.5-pro", "gpt-4o")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of available tool configurations
            tool_choice: Preference for tool usage ("auto", "any", "none")
            **kwargs: Additional provider-specific configurations
            
        Returns:
            Dict containing standardized response format:
            {
                "content": str | None,
                "tool_calls": List[Dict] | None,
                "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
                "finish_reason": str,
            }
        """
        pass

    @abstractmethod
    async def get_token_count(self, messages: List[Dict[str, Any]], model: str) -> int:
        """Calculate the estimated token count for the given messages and model."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the internal identifier for this provider."""
        pass
