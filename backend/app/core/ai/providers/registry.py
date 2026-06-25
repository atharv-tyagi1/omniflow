from typing import Dict, Type
from backend.app.core.ai.providers.base import BaseProvider
from backend.app.core.ai.providers.gemini_provider import GeminiProvider
from backend.app.core.ai.providers.openai_provider import OpenAIProvider
from backend.app.core.ai.providers.anthropic_provider import AnthropicProvider
from backend.app.core.agent.exceptions import ProviderError

class ProviderRegistry:
    """
    Registry for resolving and instantiating the correct LLM provider.
    """
    _providers: Dict[str, Type[BaseProvider]] = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> BaseProvider:
        """
        Returns an instance of the requested provider.
        """
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ProviderError(f"Provider '{provider_name}' is not supported or registered.")
        return provider_class()
