"""Sentiment model — AI-analyzed sentiment scores for conversations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class Sentiment(Base):
    __tablename__ = "sentiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    score = Column(Numeric(5, 2), nullable=False)
    label = Column(String(20), nullable=False)  # positive | negative | neutral
    analyzed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="sentiments", lazy="selectin")

    __table_args__ = (
        Index("idx_sentiments_label", "label"),
    )

    def __repr__(self) -> str:
        return f"<Sentiment {self.label} ({self.score})>"
