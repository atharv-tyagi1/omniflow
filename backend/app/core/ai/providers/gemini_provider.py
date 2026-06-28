"""Gemini Provider implementation."""

from typing import Any, Dict, List, Optional
import time
import json
import asyncio
from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from pydantic import BaseModel

from backend.app.core.ai.providers.base import BaseProvider
from backend.app.core.config import settings
import os

class GeminiProvider(BaseProvider):
    """Implementation of BaseProvider for Google Gemini models."""
    
    def __init__(self):
        self._client = None

    def _initialize(self):
        if not self._client:
            api_key = getattr(settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
            if not api_key:
                raise ValueError("GEMINI_API_KEY is missing. Cannot initialize GeminiProvider.")
            self._client = genai.Client(api_key=api_key)

    def get_provider_name(self) -> str:
        return "gemini"

    async def get_token_count(self, messages: List[Dict[str, Any]], model: str) -> int:
        """Estimates token count."""
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
        """Generic, robust text generation wrapper with retry logic, latency tracking."""
        self._initialize()
        start_time = time.time()
        
        # Convert simple messages to Gemini Contents
        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            if m["role"] == "system":
                continue # We will pull out system messages
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
            
        # Combine system messages into the config system_instruction if present
        system_msgs = [m.get("content", "") for m in messages if m["role"] == "system"]
        
        config_kwargs = {"temperature": temperature}
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens
            
        if system_msgs:
            config_kwargs["system_instruction"] = "\n".join(system_msgs)
            
        # Handle JSON schema for legacy wrappers
        response_schema = kwargs.get("response_schema")
        if response_schema and issubclass(response_schema, BaseModel):
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema
            
        config = types.GenerateContentConfig(**config_kwargs)

        # If there are no contents (e.g., only system message), we must provide at least one user message
        if not contents and system_msgs:
            contents = [{"role": "user", "parts": [{"text": "Proceed."}]}]

        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                result = self._client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                
                latency_ms = (time.time() - start_time) * 1000
                tokens_used = result.usage_metadata.total_token_count if result.usage_metadata else 0
                raw_text = result.text or ""
                
                structured_data = None
                if response_schema:
                    clean_text = raw_text.strip()
                    if clean_text.startswith("```"):
                        clean_text = clean_text.split("```")[1]
                        if clean_text.startswith("json"):
                            clean_text = clean_text[4:]
                    try:
                        structured_data = json.loads(clean_text.strip())
                    except json.JSONDecodeError:
                        pass
                
                # We will map it to the standardized dict
                tool_calls = None
                
                return {
                    "content": raw_text,
                    "structured_data": structured_data,
                    "tool_calls": tool_calls,
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": tokens_used,
                        "total_tokens": tokens_used
                    },
                    "latency_ms": round(latency_ms, 2),
                    "tokens_used": tokens_used,
                    "finish_reason": "stop",
                    "error": None
                }
                
            except (ResourceExhausted, ServiceUnavailable) as e:
                if attempt == max_retries - 1:
                    return {
                        "content": "",
                        "structured_data": None,
                        "tool_calls": None,
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        "latency_ms": round((time.time() - start_time) * 1000, 2),
                        "tokens_used": 0,
                        "finish_reason": "error",
                        "error": "Gemini API rate limit exceeded or service unavailable."
                    }
                await asyncio.sleep(base_delay * (2 ** attempt))
            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "API_KEY" in error_msg.upper():
                    error_msg = "Invalid Gemini API key. Please check your config."
                    
                return {
                    "content": "",
                    "structured_data": None,
                    "tool_calls": None,
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                    "tokens_used": 0,
                    "finish_reason": "error",
                    "error": f"AI Error: {error_msg}"
                }
