import os
import json
import logging
from dataclasses import dataclass
from typing import Optional
from google import genai

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Approved intent categories — must align with the four approved agents in Master Build Instructions
VALID_INTENTS = {"sales", "support", "customer_care", "unknown"}


@dataclass
class IntentResult:
    """Structured output from the Router Agent, per the mandated output format."""

    primary_intent: str
    secondary_intent: Optional[str]
    confidence: float

    def to_dict(self) -> dict:
        return {
            "primary_intent": self.primary_intent,
            "secondary_intent": self.secondary_intent,
            "confidence": self.confidence,
        }


class IntentRouter:
    """
    Router Agent — classifies incoming customer messages using Gemini.

    Mandated output format (Master Build Instructions §ROUTER AGENT RULES):
        {
            "primary_intent":   "<sales|support|customer_care|unknown>",
            "secondary_intent": "<sales|support|customer_care|unknown|null>",
            "confidence":        0.00
        }

    Gemini is used exclusively as a classification engine; it never directly
    communicates with the user (AI Architecture Rules §GEMINI USAGE RULES).
    """

    _client: Optional[genai.Client] = None

    SYSTEM_PROMPT = """You are the OmniFlow Router Agent.

Your ONLY job is to classify a customer message and return a JSON object.
You must NEVER reply with conversational text.
You must ALWAYS return valid JSON, nothing else.

Approved intent categories:
- "sales"         → customer wants to buy, learn about products, pricing, or upgrade
- "support"       → customer has a technical problem, bug, or needs troubleshooting help
- "customer_care" → customer is frustrated, upset, seeking empathy, complaint, refund
- "unknown"       → message is ambiguous or cannot be classified

Required JSON output format:
{
    "primary_intent": "<intent>",
    "secondary_intent": "<intent or null>",
    "confidence": <float between 0.0 and 1.0>
}

Rules:
- primary_intent MUST be one of: sales, support, customer_care, unknown
- secondary_intent can be any approved intent or null
- confidence MUST be a float, never a percentage string
- Return ONLY the JSON object, no markdown, no explanation"""

    @classmethod
    def _get_client(cls) -> genai.Client:
        if cls._client is None:
            api_key = getattr(
                settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY")
            )
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not configured.")
            cls._client = genai.Client(api_key=api_key)
        return cls._client

    @classmethod
    async def classify(
        cls, message: str, conversation_history: Optional[list[str]] = None
    ) -> IntentResult:
        """
        Classifies a customer message into one of the approved agent categories.

        Args:
            message: The raw customer message text.
            conversation_history: Optional list of prior messages for context (last N turns).

        Returns:
            IntentResult with primary_intent, secondary_intent, and confidence.
        """
        client = cls._get_client()

        # Build context-aware prompt
        context_block = ""
        if conversation_history:
            context_block = (
                "Recent conversation context:\n"
                + "\n".join(conversation_history[-6:])
                + "\n\n"
            )

        prompt = f'{context_block}Customer message to classify:\n"{message}"'

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    {"role": "user", "parts": [{"text": cls.SYSTEM_PROMPT}]},
                    {
                        "role": "model",
                        "parts": [
                            {"text": "Understood. I will respond only with valid JSON."}
                        ],
                    },
                    {"role": "user", "parts": [{"text": prompt}]},
                ],
            )

            raw_text = response.text.strip()

            # Strip markdown code fences if the model wraps in ```json
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            parsed = json.loads(raw_text)

            primary = parsed.get("primary_intent", "unknown")
            secondary = parsed.get("secondary_intent")
            confidence = float(parsed.get("confidence", 0.0))

            # Sanitize: enforce only approved intent values
            if primary not in VALID_INTENTS:
                logger.warning(
                    f"Gemini returned invalid primary intent '{primary}', defaulting to 'unknown'"
                )
                primary = "unknown"
            if secondary and secondary not in VALID_INTENTS:
                secondary = None

            return IntentResult(
                primary_intent=primary,
                secondary_intent=secondary,
                confidence=round(confidence, 4),
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"IntentRouter failed to parse Gemini response: {e}")
            return IntentResult(
                primary_intent="unknown", secondary_intent=None, confidence=0.0
            )
        except Exception as e:
            logger.error(f"IntentRouter encountered an unexpected error: {e}")
            return IntentResult(
                primary_intent="unknown", secondary_intent=None, confidence=0.0
            )
