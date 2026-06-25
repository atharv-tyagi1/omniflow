"""WorkflowEdge model — defines directed edges between nodes."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class WorkflowEdge(Base):
    __tablename__ = "workflow_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_node_id = Column(UUID(as_uuid=True), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), nullable=False)
    source_handle = Column(String(100), nullable=True)
    target_handle = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    version = relationship("WorkflowVersion", back_populates="edges", lazy="selectin")

    __table_args__ = (
        Index("idx_workflow_edges_version", "version_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowEdge {self.source_node_id} -> {self.target_node_id}>"
