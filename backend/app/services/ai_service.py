from typing import List, Dict, Any, Optional
import logging

from backend.app.schemas.ai import AIRequest, AIResponse
from backend.app.core.ai.gemini_client import GeminiClient
from backend.app.core.ai.prompt_builder import PromptBuilder
from backend.app.core.ai.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

class AIService:
    """
    Central Orchestration Layer for all AI generation.
    Connects PromptBuilder, GeminiClient, and RateLimiter.
    """

    @staticmethod
    async def generate_response(request: AIRequest) -> AIResponse:
        """
        Takes an AIRequest, checks limits, builds the prompt, calls the LLM,
        and returns a standardized AIResponse.
        """
        # 1. Rate Limiting Check
        rate_status = rate_limiter.check()
        if not rate_status["allowed"]:
            logger.warning(f"AI Service rate limited: {rate_status['error']}")
            return AIResponse(
                content="",
                error=rate_status["error"],
                latency_ms=0.0,
                tokens_used=0,
                sources=[]
            )

        # 2. Build the exact prompt string
        full_prompt = PromptBuilder.build_prompt(
            system_prompt=request.system_prompt,
            user_query=request.user_query,
            conversation_history=request.conversation_history,
            rag_context=request.rag_context
        )
        
        logger.info("Dispatching prompt to Gemini API...")

        # 3. Call Gemini via the hardened client wrapper
        result = await GeminiClient.generate_completion(
            prompt=full_prompt,
            response_schema=request.response_schema,
            model="gemini-2.0-flash" # Defaulting to flash for latency/cost efficiency
        )

        # 4. Record successful invocation if no structural API errors
        if not result.get("error"):
            rate_limiter.record()

        # 5. Return standardized payload
        return AIResponse(
            content=result.get("content", ""),
            structured_data=result.get("structured_data"),
            latency_ms=result.get("latency_ms", 0.0),
            tokens_used=result.get("tokens_used", 0),
            sources=[], # Populated by callers holding RAG context mapping
            error=result.get("error")
        )
