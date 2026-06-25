"""AgentToolPolicy model — tool permission configuration."""

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentToolPolicy(Base):
    __tablename__ = "agent_tool_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_type = Column(String(50), nullable=False)
    tool_config = Column(JSONB, nullable=False, default=dict)
    allowed_inputs = Column(JSONB, nullable=True)
    allowed_outputs = Column(JSONB, nullable=True)
    rate_limit = Column(Integer, nullable=True)
    approval_required = Column(Boolean, nullable=False, default=False)

    # Relationships
    version = relationship("AgentVersion", backref="tool_policies")

    def __repr__(self) -> str:
        return f"<AgentToolPolicy {self.tool_type} for v{self.version_id}>"
