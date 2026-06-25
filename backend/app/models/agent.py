"""Agent model — metadata for Agent Instances."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    avatar_url = Column(String(1000), nullable=True)
    is_public_allowed = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
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
    template = relationship("AgentTemplate", lazy="selectin")

    __table_args__ = (
        Index("idx_agents_workspace", "workspace_id"),
    )

    def __repr__(self) -> str:
        return f"<Agent {self.name} ({self.id})>"
