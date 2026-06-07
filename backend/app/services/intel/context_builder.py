"""Phase 13: Conversation Context Builder."""

import re
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.models.message import Message


class ConversationContextBuilder:
    """Builds a bounded context window for Gemini analysis."""

    # PII Sanitization Patterns
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    PHONE_PATTERN = re.compile(r'\+?\d[\d\s\-\(\)]{7,14}\d')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    # Credit card: 13-19 digits, optionally separated by spaces or hyphens
    CC_PATTERN = re.compile(r'\b(?:\d[ -]*?){13,19}\b')

    @classmethod
    def sanitize_pii(cls, text: str) -> str:
        """Redact known PII patterns.
        
        Order matters: apply more specific patterns (SSN, CC) before
        the broader phone pattern to prevent greedy phone matching
        from consuming SSN/CC digit sequences.
        """
        if not text:
            return ""
        # 1. Most specific patterns first
        text = cls.SSN_PATTERN.sub("[REDACTED_ID]", text)
        text = cls.CC_PATTERN.sub("[REDACTED_CC]", text)
        # 2. Then broader patterns
        text = cls.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
        text = cls.PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
        return text

    @classmethod
    async def build_context(
        cls,
        db: AsyncSession,
        conversation_id: UUID,
        max_messages: int = 20
    ) -> Dict[str, Any]:
        """
        Builds a safe, bounded context string avoiding full transcripts.
        """
        # Fetch the most recent messages (sliding window)
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(max_messages)
        )
        result = await db.execute(stmt)
        # Reverse to chronological order
        messages = list(result.scalars().all())[::-1]

        transcript_lines = []
        for msg in messages:
            sender = msg.sender_type.upper() if msg.sender_type else "UNKNOWN"
            content = cls.sanitize_pii(msg.content)
            transcript_lines.append(f"{sender}: {content}")

        transcript_block = "\n".join(transcript_lines)

        return {
            "conversation_id": str(conversation_id),
            "bounded_transcript": transcript_block,
            "message_count_included": len(messages)
        }
