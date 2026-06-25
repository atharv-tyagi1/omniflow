"""Channel model — workspace communication endpoints."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_type = Column(String(50), nullable=False)  # website, telegram, whatsapp, slack, discord, api, voice
    config = Column(JSONB, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")

    __table_args__ = (
        Index("idx_channels_workspace", "workspace_id"),
    )

    def __repr__(self) -> str:
        return f"<Channel {self.channel_type} ({self.id})>"
