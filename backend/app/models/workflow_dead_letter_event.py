"""WorkflowDeadLetterEvent model — stores events that permanently failed."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.models.base import Base


class WorkflowDeadLetterEvent(Base):
    __tablename__ = "workflow_dead_letter_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type = Column(String(255), nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)
    error_reason = Column(String(1000), nullable=True)
    failed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_workflow_dead_letter_events_workspace", "workspace_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowDeadLetterEvent {self.event_type}>"
