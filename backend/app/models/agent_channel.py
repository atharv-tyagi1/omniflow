"""AgentChannel model — maps agents to channels."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentChannel(Base):
    __tablename__ = "agent_channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    channel = relationship("Channel", backref="agent_mappings")
    agent = relationship("Agent", backref="channel_mappings")

    __table_args__ = (
        Index("idx_agent_channels_workspace", "workspace_id"),
        UniqueConstraint("channel_id", "agent_id", name="uq_agent_channels_mapping"),
    )

    def __repr__(self) -> str:
        return f"<AgentChannel {self.agent_id} -> {self.channel_id}>"
