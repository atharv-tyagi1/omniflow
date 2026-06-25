"""AgentPrompt model — prompt system configuration."""

import uuid

from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentPrompt(Base):
    __tablename__ = "agent_prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    system_prompt = Column(Text, nullable=False)
    welcome_prompt = Column(Text, nullable=True)
    fallback_prompt = Column(Text, nullable=True)

    # Relationships
    version = relationship("AgentVersion", backref="prompt_config")

    def __repr__(self) -> str:
        return f"<AgentPrompt for v{self.version_id}>"
