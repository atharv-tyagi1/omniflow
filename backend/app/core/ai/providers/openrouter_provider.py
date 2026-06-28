"""OpenRouter Provider — routes to 300+ models via a single OpenAI-compatible API."""

import logging
import time
from typing import Any, Dict, List, Optional

from backend.app.core.ai.providers.base import BaseProvider
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(BaseProvider):
    """
    Provider implementation for OpenRouter (openrouter.ai).
    Compatible with the OpenAI chat completions API format.
    Supports 300+ models from Anthropic, Google, Meta, Mistral, etc.
    """

    def get_provider_name(self) -> str:
        return "openrouter"

    async def get_token_count(self, messages: List[Dict[str, Any]], model: str) -> int:
        return sum(len(str(m.get("content", ""))) // 4 for m in messages)

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
        """Generates a completion via OpenRouter's OpenAI-compatible API."""
        api_key = settings.OPENROUTER_API_KEY
        if not api_key:
            logger.warning("OPENROUTER_API_KEY is not configured — provider unavailable.")
            return {
                "content": None,
                "tool_calls": None,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "finish_reason": "error",
                "error": "OpenRouter API key not configured",
            }

        try:
            import httpx

            payload: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice or "auto"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://omniflow.ai",
                "X-Title": "OmniFlow Agent Runtime",
            }

            start = time.time()
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{_OPENROUTER_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

            latency_ms = int((time.time() - start) * 1000)
            data = response.json()

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = data.get("usage", {})

            logger.info(
                f"OpenRouter {model} completed: "
                f"tokens={usage.get('total_tokens', 0)} latency={latency_ms}ms"
            )

            return {
                "content": message.get("content"),
                "tool_calls": message.get("tool_calls"),
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                "finish_reason": choice.get("finish_reason", "stop"),
            }

        except Exception as e:
            logger.error(f"OpenRouter provider failed for model {model}: {e}")
            return {
                "content": None,
                "tool_calls": None,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "finish_reason": "error",
                "error": str(e),
            }
