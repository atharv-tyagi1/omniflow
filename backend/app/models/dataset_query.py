"""DatasetQuery model — natural-language queries against datasets."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class DatasetQuery(Base):
    __tablename__ = "dataset_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    chart_config = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    dataset = relationship("Dataset", back_populates="queries", lazy="selectin")

    __table_args__ = (Index("idx_dataset_queries_dataset", "dataset_id"),)

    def __repr__(self) -> str:
        return f"<DatasetQuery {self.id}>"
