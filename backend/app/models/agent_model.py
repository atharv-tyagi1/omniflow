"""AgentModel model — reasoning layer model configuration."""

import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AgentModel(Base):
    __tablename__ = "agent_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    provider = Column(String(50), nullable=False)
    model_name = Column(String(255), nullable=False)
    config = Column(JSONB, nullable=False, default=dict)

    # Relationships
    version = relationship("AgentVersion", backref="model_config")

    def __repr__(self) -> str:
        return f"<AgentModel {self.provider}/{self.model_name}>"
