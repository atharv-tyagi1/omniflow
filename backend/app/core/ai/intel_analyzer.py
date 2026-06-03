import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from google import genai
from google.genai import types

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class IntelResult(BaseModel):
    sentiment_label: str = Field(
        description="The overall sentiment of the customer: 'positive', 'neutral', or 'negative'"
    )
    sentiment_score: float = Field(
        description="A score from -1.0 (very negative) to 1.0 (very positive)"
    )
    topics: List[str] = Field(
        description="Top 1 to 3 main topics discussed in the conversation, maximum 3 words per topic (e.g., 'Billing Issue', 'Refund Request')"
    )


class IntelAnalyzer:
    SYSTEM_PROMPT = """You are a highly intelligent business analyst AI.
Your job is to read a conversation transcript between a customer and an AI agent, and extract the underlying sentiment and main topics.
Be completely objective. Base the sentiment strictly on the customer's attitude and language.
Output exactly in the provided JSON schema.
"""

    @classmethod
    async def analyze(cls, conversation_history: List[str]) -> Optional[IntelResult]:
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY is not set.")
            return None

        transcript = "\n\n".join(conversation_history)

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=transcript,
                config=types.GenerateContentConfig(
                    system_instruction=cls.SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=IntelResult,
                    temperature=0.0,
                ),
            )

            result_dict = json.loads(response.text)
            return IntelResult(**result_dict)

        except Exception as e:
            logger.error(f"IntelAnalyzer failed: {e}")
            return None
