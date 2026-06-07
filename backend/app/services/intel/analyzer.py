"""Phase 13: Conversation Analyzer."""

import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.ai.gemini_client import GeminiClient
from backend.app.services.intel.context_builder import ConversationContextBuilder

logger = logging.getLogger(__name__)


class IntelAnalysisError(Exception):
    """Raised when Gemini analysis fails in a potentially transient way.
    
    This causes the IntelWorker to retry the event rather than silently
    marking it as processed. Permanent failures are bounded by MAX_ATTEMPTS.
    """
    pass


class ConversationAnalyzer:
    """Analyzes conversation contexts using LLMs to extract insights."""

    ANALYZER_VERSION = "1.0.0"
    SCHEMA_VERSION = 1

    @classmethod
    async def analyze_conversation(
        cls,
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a conversation, extracting intent, topics, sentiment, and a summary.
        Uses a bounded context to avoid full transcript costs.
        
        Returns:
            dict with analysis results on success.
            None ONLY for genuinely empty conversations (no messages to analyze).
        
        Raises:
            IntelAnalysisError on Gemini failures or malformed responses,
            allowing the worker retry logic to handle transient issues.
        """
        context = await ConversationContextBuilder.build_context(db, conversation_id)
        if not context["bounded_transcript"].strip():
            logger.info(f"Skipping intel extraction for empty conversation: {conversation_id}")
            return None

        prompt = f"""
You are a highly analytical conversation intelligence AI.
Extract intelligence from the following customer conversation transcript.

Transcript:
{context["bounded_transcript"]}

Respond EXACTLY in this JSON structure:
{{
  "primary_intent": "pricing_request", // e.g. refund_request, technical_support, general_inquiry
  "secondary_intents": ["billing_issue"], // array of secondary intent strings
  "sentiment": "positive", // positive, neutral, negative, frustrated, excited
  "resolution": "resolved", // resolved, unresolved, escalated, abandoned
  "topics": ["pricing", "features"], // array of key subjects discussed
  "short_summary": "Customer asked about pricing.", // 1-2 sentence overview
  "long_summary": "The customer initiated the chat to inquire about enterprise pricing. They were routed to sales.", // Detailed summary
  "confidence_score": 0.85, // 0.0 to 1.0 confidence in overall analysis
  "review_reason": null // null if confident, or a short string like "ambiguous_intent" if confidence is low
}}
"""
        response = await GeminiClient.generate_completion(prompt)

        # Check for Gemini-level errors (rate limit, service unavailable, API key)
        gemini_error = response.get("error")
        if gemini_error:
            raise IntelAnalysisError(f"Gemini error for conversation {conversation_id}: {gemini_error}")

        response_text = response.get("content", "")
        if not response_text.strip():
            raise IntelAnalysisError(f"Gemini returned empty response for conversation {conversation_id}")

        try:
            # Strip markdown formatting if any
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
            
            data = json.loads(response_text.strip())
            
            # Sanitize PII from summaries
            data["short_summary"] = ConversationContextBuilder.sanitize_pii(data.get("short_summary", ""))
            data["long_summary"] = ConversationContextBuilder.sanitize_pii(data.get("long_summary", ""))
            
            # Assess needs_review
            confidence = float(data.get("confidence_score", 0.0))
            data["needs_review"] = confidence < 0.70
            
            return data
            
        except json.JSONDecodeError as e:
            raise IntelAnalysisError(
                f"Failed to parse intelligence JSON for conversation {conversation_id}: {e}. "
                f"Raw response (first 200 chars): {response_text[:200]}"
            )
        except Exception as e:
            raise IntelAnalysisError(
                f"Unexpected error processing Gemini response for conversation {conversation_id}: {e}"
            )
