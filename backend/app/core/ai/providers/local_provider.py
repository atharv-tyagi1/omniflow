"""Local LLM Provider Stub."""

from typing import Dict, Any, List
from backend.app.core.ai.providers.base import BaseProvider

class LocalProvider(BaseProvider):
    """Adapter for Local LLMs (e.g., Ollama, vLLM)."""

    async def generate_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.0,
        tools: List[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using a Local LLM."""
        raise NotImplementedError("Local LLM provider is not yet fully implemented.")
