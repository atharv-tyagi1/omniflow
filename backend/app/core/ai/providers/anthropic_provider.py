from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

from backend.app.core.ai.providers.base import BaseProvider
from backend.app.core.agent.exceptions import ProviderError

class AnthropicProvider(BaseProvider):
    """
    Stub adapter for Anthropic API.
    To be fully implemented in a future phase.
    """

    async def generate_completion(
        self,
        prompt: str,
        response_schema: Optional[Type[BaseModel]] = None,
        model: str = "claude-3-5-sonnet",
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Placeholder for Anthropic completion logic.
        """
        raise ProviderError("AnthropicProvider is currently a stub and not yet implemented.")
