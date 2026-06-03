"""VoiceInteraction model — voice call recordings and transcripts."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class VoiceInteraction(Base):
    __tablename__ = "voice_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    audio_url = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="voice_interactions", lazy="selectin")

    __table_args__ = (
        Index("idx_voice_conversation", "conversation_id"),
    )

    def __repr__(self) -> str:
        return f"<VoiceInteraction {self.id}>"
