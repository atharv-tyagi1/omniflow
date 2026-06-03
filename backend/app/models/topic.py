"""Topic model — AI-extracted topics from conversations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_name = Column(String(255), nullable=False)
    confidence = Column(Numeric(5, 2), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    conversation = relationship(
        "Conversation", back_populates="topics", lazy="selectin"
    )

    __table_args__ = (Index("idx_topics_name", "topic_name"),)

    def __repr__(self) -> str:
        return f"<Topic {self.topic_name} ({self.confidence})>"
