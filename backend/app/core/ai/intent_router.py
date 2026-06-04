import logging
from typing import Optional

from backend.app.schemas.router import IntentResult, AgentIntent
from backend.app.schemas.ai import AIRequest
from backend.app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class IntentRouter:
    """
    Router Agent — classifies incoming customer messages using AIService.
    Returns a strict IntentResult schema.
    """

    SYSTEM_PROMPT = """You are the OmniFlow Router Agent.
Your ONLY job is to classify a customer message into an intent.

Approved intent categories:
- "sales"         → customer wants to buy, learn about products, pricing, or upgrade
- "support"       → customer has a technical problem, bug, or needs troubleshooting help
- "customer_care" → customer is frustrated, upset, seeking empathy, complaint, refund
- "unknown"       → message is ambiguous or cannot be classified

Evaluate the user message and optionally the conversation history to determine the primary intent, an optional secondary intent, and your confidence score (0.0 to 1.0)."""

    @classmethod
    async def classify(
        cls, message: str, conversation_history: Optional[list[str]] = None
    ) -> IntentResult:
        """
        Classifies a customer message into one of the approved agent categories.
        """
        request = AIRequest(
            user_query=message,
            system_prompt=cls.SYSTEM_PROMPT,
            conversation_history=conversation_history,
            response_schema=IntentResult
        )

        response = await AIService.generate_response(request)

        if response.error or not response.structured_data:
            logger.error(f"IntentRouter classification failed: {response.error}")
            return IntentResult(
                primary_intent=AgentIntent.UNKNOWN,
                secondary_intent=None,
                confidence=0.0
            )

        try:
            return IntentResult(**response.structured_data)
        except Exception as e:
            logger.error(f"IntentRouter failed to parse AIService output: {e}")
            return IntentResult(
                primary_intent=AgentIntent.UNKNOWN,
                secondary_intent=None,
                confidence=0.0
            )
