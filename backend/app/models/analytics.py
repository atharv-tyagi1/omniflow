"""
Phase 12: Analytics database models.
AnalyticsEvent — raw event store with idempotency key and schema versioning.
AnalyticsOutbox — durable outbox for transactional event delivery.
AnalyticsHourlyRollup / AnalyticsDailyRollup — pre-aggregated metric tables.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from backend.app.models.base import Base


class AnalyticsOutbox(Base):
    """
    Durable outbox table. Events are written here inside the same DB
    transaction as the business action, then processed asynchronously
    by the analytics worker.
    """
    __tablename__ = "analytics_outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True)

    event_type = Column(String(80), nullable=False)
    source_agent = Column(String(50), nullable=True)
    target_agent = Column(String(50), nullable=True)
    event_metadata = Column(JSONB, nullable=True)
    idempotency_key = Column(String(255), nullable=True, index=True)
    schema_version = Column(Integer, nullable=False, default=1)

    # Processing state
    status = Column(String(20), nullable=False, default="pending")  # pending | processed | failed
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_outbox_status_created", "status", "created_at"),
    )


class AnalyticsEvent(Base):
    """
    Canonical event store. Populated by the analytics worker from the outbox.
    """
    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    event_type = Column(String(80), nullable=False, index=True)
    source_agent = Column(String(50), nullable=True)
    target_agent = Column(String(50), nullable=True)
    event_metadata = Column(JSONB, nullable=True)

    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    schema_version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("ix_analytics_events_ws_type_date", "workspace_id", "event_type", "created_at"),
    )


class AnalyticsHourlyRollup(Base):
    """Pre-aggregated hourly metric rollup. One row per workspace/metric/hour/dimension."""
    __tablename__ = "analytics_hourly_rollups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)

    time_bucket = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_name = Column(String(80), nullable=False, index=True)
    dimension = Column(JSONB, nullable=True)  # structured key/value breakdown
    value = Column(Numeric(14, 4), nullable=False, default=0)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_hr_ws_bucket_metric", "workspace_id", "time_bucket", "metric_name"),
    )


class AnalyticsDailyRollup(Base):
    """Pre-aggregated daily metric rollup. One row per workspace/metric/day/dimension."""
    __tablename__ = "analytics_daily_rollups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)

    time_bucket = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_name = Column(String(80), nullable=False, index=True)
    dimension = Column(JSONB, nullable=True)
    value = Column(Numeric(14, 4), nullable=False, default=0)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_dr_ws_bucket_metric", "workspace_id", "time_bucket", "metric_name"),
    )
