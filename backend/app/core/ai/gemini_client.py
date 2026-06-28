import os
from typing import List, Dict, Any, Optional
from google import genai
from backend.app.core.config import settings
from backend.app.core.ai.providers.registry import provider_registry


class GeminiClient:
    """
    Thin adapter for legacy code to route traffic through the unified Provider Abstraction.
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
            from google.genai import types
            result = cls._client.models.embed_content(
                model="gemini-embedding-2",
                contents=batch,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            for embedding_obj in result.embeddings:
                all_embeddings.append(embedding_obj.values)
        return all_embeddings

    @classmethod
    def embed_query(cls, text: str) -> List[float]:
        """
        Generates an embedding for a search query.
        """
        cls._initialize()
        from google.genai import types
        result = cls._client.models.embed_content(
            model="gemini-embedding-2",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=768)
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
        Thin adapter: Routes this legacy call to the unified Provider Abstraction.
        """
        provider = provider_registry.get_provider("gemini")
        messages = [{"role": "user", "content": prompt}]
        
        result = await provider.generate_completion(
            messages=messages,
            model=model,
            response_schema=response_schema
        )
        
        return result
