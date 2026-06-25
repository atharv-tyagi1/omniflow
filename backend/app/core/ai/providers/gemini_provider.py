from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

from backend.app.core.ai.providers.base import BaseProvider
from backend.app.core.ai.gemini_client import GeminiClient

class GeminiProvider(BaseProvider):
    """
    Implementation of the provider interface for Google Gemini.
    Acts as a thin adapter around the legacy GeminiClient.
    """

    async def generate_completion(
        self,
        prompt: str,
        response_schema: Optional[Type[BaseModel]] = None,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Delegates the completion request to the GeminiClient.
        """
        # We can pass temperature if GeminiClient is updated to accept it,
        # but for now we just use its default signature which hardcodes 0.2
        # or we could update GeminiClient to accept temperature.
        # Given the instruction not to break legacy paths, we just call it.
        
        return await GeminiClient.generate_completion(
            prompt=prompt,
            response_schema=response_schema,
            model=model
        )
