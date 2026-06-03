"""Document model — uploaded knowledge-base documents within a workspace."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_url = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending | processing | ready | failed
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    workspace = relationship("Workspace", lazy="selectin")
    uploader = relationship("User", lazy="selectin")
    chunks = relationship("DocumentChunk", back_populates="document", lazy="selectin")

    __table_args__ = (
        Index("idx_documents_workspace", "workspace_id"),
        Index("idx_documents_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Document {self.name} ({self.id})>"
