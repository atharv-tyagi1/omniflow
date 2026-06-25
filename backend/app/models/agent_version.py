"""AgentVersion model — immutable versions for Agents."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentVersion(Base):
    __tablename__ = "agent_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False)
    is_published = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    agent = relationship("Agent", lazy="selectin")
    # Cascades for prompt, model, tool_policies will be defined in their respective models
    
    __table_args__ = (
        Index("idx_agent_versions_agent", "agent_id"),
        UniqueConstraint("agent_id", "version_number", name="uq_agent_id_version_number"),
        Index(
            "idx_one_published_version",
            "agent_id",
            unique=True,
            postgresql_where=(is_published == True),
        ),
    )

    def __repr__(self) -> str:
        return f"<AgentVersion {self.agent_id} v{self.version_number}>"
