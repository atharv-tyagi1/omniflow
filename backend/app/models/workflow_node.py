"""WorkflowNode model — stores nodes within a workflow version."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    type = Column(String(100), nullable=False)
    config = Column(JSONB, nullable=False, default=dict)
    ui_position = Column(JSONB, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    version = relationship("WorkflowVersion", back_populates="nodes", lazy="selectin")

    __table_args__ = (
        Index("idx_workflow_nodes_version", "version_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowNode {self.type} ({self.id})>"
