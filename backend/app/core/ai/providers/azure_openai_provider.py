"""Azure OpenAI LLM Provider Stub."""

from typing import Dict, Any, List
from backend.app.core.ai.providers.base import BaseProvider

class AzureOpenAIProvider(BaseProvider):
    """Adapter for Azure OpenAI."""

    async def generate_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 0.0,
        tools: List[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using Azure OpenAI."""
        raise NotImplementedError("Azure OpenAI provider is not yet fully implemented.")
