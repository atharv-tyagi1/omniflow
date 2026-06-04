import os
from typing import List
from google import genai
from backend.app.core.config import settings


class GeminiClient:
    """
    Singleton-style wrapper for the modern Google GenAI SDK, enforcing strict
    model selection and batching for embedding generation.
    """

    _client = None

    SYSTEM_PROMPT = """You are AI Business Analyst, an expert business intelligence assistant.

Your role:
- Analyze business questions and provide clear, actionable insights
- When given data context, generate relevant analysis
- Present numbers clearly with comparisons and trends
- Keep responses concise and well-structured
- Use bullet points and sections for clarity
- If a question is vague, provide a helpful general analysis
- If you cannot answer something, explain what data would be needed

Response format:
- Use markdown formatting for readability
- Bold key numbers and metrics
- Use bullet points for lists
- Keep responses under 300 words unless detailed analysis is requested"""

    @classmethod
    def _initialize(cls):
        if not cls._client:
            api_key = getattr(
                settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY")
            )
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY is missing. Cannot initialize GeminiClient."
                )
            cls._client = genai.Client(api_key=api_key)

    @classmethod
    def generate_embeddings(
        cls, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generates 768-dimensional embeddings using text-embedding-004.
        Implements chunk batching to avoid API payload limits.
        """
        cls._initialize()

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            result = cls._client.models.embed_content(
                model="text-embedding-004",
                contents=batch,
            )

            # Extract embeddings from the new SDK result format
            for embedding_obj in result.embeddings:
                all_embeddings.append(embedding_obj.values)

        return all_embeddings

    @classmethod
    def embed_query(cls, text: str) -> List[float]:
        """
        Generates an embedding for a search query.
        """
        cls._initialize()

        result = cls._client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )
        return result.embeddings[0].values

    @classmethod
    async def generate_completion(
        cls,
        prompt: str,
        response_schema=None,
        model: str = "gemini-2.0-flash",
    ) -> dict:
        """
        Generic, robust text generation wrapper with retry logic, latency tracking,
        and structured output support.
        
        Returns:
            dict: {
                "content": str,
                "structured_data": dict | None,
                "latency_ms": float,
                "tokens_used": int,
                "error": str | None
            }
        """
        cls._initialize()
        
        import time
        import json
        import asyncio
        from google.genai import types
        from pydantic import BaseModel
        from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
        
        start_time = time.time()
        
        config_kwargs = {"temperature": 0.2}
        if response_schema and issubclass(response_schema, BaseModel):
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema
            
        config = types.GenerateContentConfig(**config_kwargs)

        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                result = cls._client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                
                latency_ms = (time.time() - start_time) * 1000
                tokens_used = result.usage_metadata.total_token_count if result.usage_metadata else 0
                
                response_payload = {
                    "content": "",
                    "structured_data": None,
                    "latency_ms": round(latency_ms, 2),
                    "tokens_used": tokens_used,
                    "error": None
                }
                
                raw_text = result.text or ""
                
                if response_schema:
                    try:
                        # Sometimes gemini wraps json in ```json fences
                        clean_text = raw_text.strip()
                        if clean_text.startswith("```"):
                            clean_text = clean_text.split("```")[1]
                            if clean_text.startswith("json"):
                                clean_text = clean_text[4:]
                        clean_text = clean_text.strip()
                        parsed = json.loads(clean_text)
                        response_payload["structured_data"] = parsed
                        # the "content" is somewhat meaningless for structured data, but we'll include raw
                        response_payload["content"] = raw_text
                    except json.JSONDecodeError as e:
                        response_payload["error"] = f"Failed to parse structured output: {e}"
                        response_payload["content"] = raw_text
                else:
                    response_payload["content"] = raw_text
                    
                return response_payload
                
            except (ResourceExhausted, ServiceUnavailable) as e:
                if attempt == max_retries - 1:
                    return {
                        "content": "",
                        "structured_data": None,
                        "latency_ms": round((time.time() - start_time) * 1000, 2),
                        "tokens_used": 0,
                        "error": "Gemini API rate limit exceeded or service unavailable. Please try again later."
                    }
                await asyncio.sleep(base_delay * (2 ** attempt)) # Exponential backoff
            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "API_KEY" in error_msg.upper():
                    error_msg = "Invalid Gemini API key. Please check your config."
                    
                return {
                    "content": "",
                    "structured_data": None,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                    "tokens_used": 0,
                    "error": f"AI Error: {error_msg}"
                }
