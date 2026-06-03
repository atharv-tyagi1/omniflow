from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.message import Message
from backend.app.models.sentiment import Sentiment
from backend.app.models.topic import Topic
from backend.app.core.ai.intel_analyzer import IntelAnalyzer

logger = logging.getLogger(__name__)


class IntelService:
    @staticmethod
    async def analyze_conversation(db: AsyncSession, conversation_id: UUID) -> dict:
        """
        Analyze a conversation to extract sentiment and topics, then persist them.
        """
        # Fetch all messages for the conversation
        messages_query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )

        result = await db.execute(messages_query)
        messages = result.scalars().all()

        if not messages:
            logger.warning(f"No messages found for conversation {conversation_id}")
            return {"status": "skipped", "reason": "No messages"}

        transcript = []
        for m in messages:
            sender = "Customer" if m.sender_type == "customer" else "Agent"
            transcript.append(f"{sender}: {m.content}")

        # Run Intel Analysis
        intel_result = await IntelAnalyzer.analyze(transcript)
        if not intel_result:
            logger.error(f"Intel analysis failed for conversation {conversation_id}")
            return {"status": "error", "reason": "Analysis failed"}

        # Clear old sentiments and topics if we are re-analyzing
        # For simplicity, we just add new ones, but in production we'd want to update or clear.

        sentiment = Sentiment(
            conversation_id=conversation_id,
            score=intel_result.sentiment_score,
            label=intel_result.sentiment_label,
        )
        db.add(sentiment)

        added_topics = []
        for topic_name in intel_result.topics:
            topic = Topic(
                conversation_id=conversation_id,
                topic_name=topic_name,
                confidence=None,  # We don't have per-topic confidence from Gemini right now
            )
            db.add(topic)
            added_topics.append(topic_name)

        await db.commit()

        return {
            "status": "success",
            "sentiment": intel_result.sentiment_label,
            "score": intel_result.sentiment_score,
            "topics": added_topics,
        }
