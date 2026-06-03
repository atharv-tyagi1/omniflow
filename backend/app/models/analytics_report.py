"""AnalyticsReport model — generated analytics reports stored as JSONB."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class AnalyticsReport(Base):
    __tablename__ = "analytics_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_type = Column(String(50), nullable=False)
    report_json = Column(JSONB, nullable=False)
    generated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")

    __table_args__ = (
        Index("idx_reports_workspace", "workspace_id"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsReport {self.report_type} ({self.id})>"
