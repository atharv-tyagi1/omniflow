"""AgentPermission model — RBAC mapping for Agent management."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentPermission(Base):
    __tablename__ = "agent_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(50), nullable=False)  # admin, editor, viewer
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    agent = relationship("Agent", lazy="selectin")
    user = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("idx_agent_permissions_workspace", "workspace_id"),
        UniqueConstraint("agent_id", "user_id", name="uq_agent_permissions_agent_user"),
    )

    def __repr__(self) -> str:
        return f"<AgentPermission {self.role} for User {self.user_id} on Agent {self.agent_id}>"
