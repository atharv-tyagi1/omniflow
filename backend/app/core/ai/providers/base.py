from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

class BaseProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    All providers (Gemini, OpenAI, Anthropic, etc.) must implement this interface.
    """

    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        response_schema: Optional[Type[BaseModel]] = None,
        model: str = "default",
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate a text completion or structured response.
        
        Args:
            prompt: The full assembled prompt string.
            response_schema: Optional Pydantic BaseModel for structured JSON output.
            model: The specific model ID to use (provider-specific).
            temperature: LLM sampling temperature.
            
        Returns:
            Dict containing:
                - "content": str (raw text response)
                - "structured_data": dict | None (if schema provided)
                - "latency_ms": float
                - "tokens_used": int
                - "error": str | None
        """
        pass
