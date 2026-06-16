"""VoiceInteraction model — voice call recordings and transcripts."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, LargeBinary, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class VoiceInteraction(Base):
    __tablename__ = "voice_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    idempotency_key = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False, default="public_voice")
    
    input_audio_ref = Column(String(1024), nullable=True)
    input_audio_sha256 = Column(String(64), nullable=True)
    input_audio_mime_type = Column(String(100), nullable=True)
    input_audio_size_bytes = Column(Integer, nullable=True)
    input_audio_bytes = Column(LargeBinary, nullable=True)
    
    transcript_text = Column(Text, nullable=True)
    
    reply_text = Column(Text, nullable=True)
    reply_audio_ref = Column(String(1024), nullable=True)
    reply_audio_bytes = Column(LargeBinary, nullable=True)
    
    status = Column(String(50), nullable=False, default="processing")
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    customer = relationship("Customer", lazy="selectin")
    conversation = relationship(
        "Conversation", back_populates="voice_interactions", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_voice_workspace", "workspace_id"),
        Index("idx_voice_conversation", "conversation_id"),
        Index("idx_voice_created_at", "created_at"),
        UniqueConstraint("workspace_id", "idempotency_key", name="uix_workspace_voice_idemp_key"),
    )

    def __repr__(self) -> str:
        return f"<VoiceInteraction {self.id}>"
