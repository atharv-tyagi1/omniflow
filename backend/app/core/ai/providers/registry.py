"""Provider Registry to dynamically resolve LLM providers."""

from typing import Dict, Type
from backend.app.core.ai.providers.base import BaseProvider
from backend.app.core.ai.providers.gemini_provider import GeminiProvider
from backend.app.core.ai.providers.openai_provider import OpenAIProvider
from backend.app.core.ai.providers.anthropic_provider import AnthropicProvider
from backend.app.core.ai.providers.openrouter_provider import OpenRouterProvider
from backend.app.core.ai.providers.azure_openai_provider import AzureOpenAIProvider
from backend.app.core.ai.providers.local_provider import LocalProvider

class ProviderRegistry:
    """Registry for AI LLM Providers. Ensures only supported providers can be used."""
    
    _providers: Dict[str, BaseProvider] = {}
    
    @classmethod
    def initialize(cls):
        """Register all supported providers."""
        cls.register("gemini", GeminiProvider())
        cls.register("openai", OpenAIProvider())
        cls.register("anthropic", AnthropicProvider())
        cls.register("openrouter", OpenRouterProvider())
        cls.register("azure_openai", AzureOpenAIProvider())
        cls.register("local", LocalProvider())

    @classmethod
    def register(cls, name: str, provider: BaseProvider):
        cls._providers[name] = provider

    @classmethod
    def get_provider(cls, name: str) -> BaseProvider:
        if not cls._providers:
            cls.initialize()
            
        provider = cls._providers.get(name.lower())
        if not provider:
            raise ValueError(f"Unsupported provider: {name}. Supported: {list(cls._providers.keys())}")
        return provider

# Initialize singleton registry access
provider_registry = ProviderRegistry
