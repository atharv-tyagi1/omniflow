"""
Phase 12: Analytics Worker — Outbox Processor & Rollup Builder.

Production topology:
    Web process  →  writes to analytics_outbox (same txn)
    Worker       →  polls outbox  →  analytics_events  →  rollups

The worker is idempotent: replaying the same outbox batch produces
identical analytics_events (via idempotency_key) and identical
rollup totals (via event.created_at bucket recalculation).

Local development: call `process_outbox_batch()` directly or from
a FastAPI BackgroundTask. Production: run as a separate process or
cron-triggered job.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from decimal import Decimal

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.app.models.analytics import (
    AnalyticsOutbox,
    AnalyticsEvent,
    AnalyticsHourlyRollup,
    AnalyticsDailyRollup,
)
from backend.app.schemas.analytics import AnalyticsEventType
from backend.app.services.analytics.metric_registry import metric_registry

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
BATCH_SIZE = 100

# Event types owned by domain-specific workers (e.g. IntelWorker).
# AnalyticsWorker must NOT process these — they stay in the outbox
# for the owning worker to pick up.
_EXCLUDED_EVENT_TYPES = frozenset({
    AnalyticsEventType.CONVERSATION_INTEL_PENDING.value,
})


def _hour_bucket(dt: datetime) -> datetime:
    """Truncate to UTC hour boundary."""
    return dt.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


def _day_bucket(dt: datetime) -> datetime:
    """Truncate to UTC day boundary."""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


class AnalyticsWorker:
    """
    Processes pending outbox records, inserts canonical events, and
    recalculates affected rollups.
    """

    @staticmethod
    async def process_outbox_batch(db: AsyncSession, batch_size: int = BATCH_SIZE) -> int:
        """
        Process up to `batch_size` pending outbox records.
        Returns the number of records successfully processed.
        """
        import time
        start_time = time.time()
        
        # 1. Fetch pending outbox records ordered by creation time
        # Using with_for_update(skip_locked=True) ensures that if multiple
        # worker processes run concurrently, they grab separate batches
        # without deadlocking or duplicate processing.
        stmt = (
            select(AnalyticsOutbox)
            .where(
                AnalyticsOutbox.status == "pending",
                AnalyticsOutbox.attempts < MAX_ATTEMPTS,
                AnalyticsOutbox.event_type.notin_(_EXCLUDED_EVENT_TYPES),
            )
            .order_by(AnalyticsOutbox.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await db.execute(stmt)
        records = result.scalars().all()

        if not records:
            return 0

        # Operational Metric: Queue depth & worker lag
        now = datetime.now(timezone.utc)
        oldest_record = records[0]
        created_at = oldest_record.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        lag_seconds = int((now - created_at).total_seconds())
        logger.info(
            "Operational Metric: Worker Batch Start",
            extra={
                "metric_name": "outbox_batch_started",
                "outbox_queue_depth_batch": len(records),
                "worker_lag_seconds": lag_seconds
            }
        )

        processed = 0
        failed = 0
        for record in records:
            try:
                await AnalyticsWorker._process_single(db, record)
                record.status = "processed"
                record.processed_at = now
                processed += 1
                logger.info(
                    "Operational Metric: Event Ingested",
                    extra={
                        "metric_name": "analytics_event_ingested",
                        "event_type": record.event_type,
                        "workspace_id": str(record.workspace_id)
                    }
                )
            except Exception as exc:
                record.attempts += 1
                record.last_error = str(exc)[:500]
                failed += 1
                if record.attempts >= MAX_ATTEMPTS:
                    record.status = "failed"
                    logger.error(
                        "Operational Metric: Event Permanently Failed",
                        extra={
                            "metric_name": "analytics_event_failed",
                            "event_type": record.event_type,
                            "workspace_id": str(record.workspace_id),
                            "error": exc.__class__.__name__
                        }
                    )
                else:
                    logger.warning(
                        "Outbox record %s attempt %d failed: %s",
                        record.id, record.attempts, exc.__class__.__name__,
                    )

        await db.commit()
        
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "Operational Metric: Rollup Batch Completed",
            extra={
                "metric_name": "rollup_duration_ms",
                "duration_ms": duration_ms,
                "processed_count": processed,
                "failed_count": failed,
                "rollup_failures": failed
            }
        )
        return processed

    @staticmethod
    async def _process_single(db: AsyncSession, record: AnalyticsOutbox) -> None:
        """Insert the canonical event and update rollups for one outbox record."""

        # ── Idempotency check ────────────────────────────────
        if record.idempotency_key:
            existing = await db.execute(
                select(AnalyticsEvent.id).where(
                    AnalyticsEvent.idempotency_key == record.idempotency_key
                ).limit(1)
            )
            if existing.scalar_one_or_none() is not None:
                logger.info("Duplicate event suppressed: %s", record.idempotency_key)
                return  # already processed — idempotent skip

        # ── Insert canonical event ───────────────────────────
        event = AnalyticsEvent(
            workspace_id=record.workspace_id,
            conversation_id=record.conversation_id,
            customer_id=record.customer_id,
            event_type=record.event_type,
            source_agent=record.source_agent,
            target_agent=record.target_agent,
            event_metadata=record.event_metadata,
            idempotency_key=record.idempotency_key,
            schema_version=record.schema_version,
            created_at=record.created_at,  # use EVENT time, not processing time
        )
        db.add(event)

        # ── Update rollups using event.created_at (not now()) ─
        try:
            event_type_enum = AnalyticsEventType(record.event_type)
        except ValueError:
            logger.warning("Unknown event_type in outbox: %s", record.event_type)
            return

        affected_metrics = metric_registry.metrics_for_event(event_type_enum)
        event_time = record.created_at or datetime.now(timezone.utc)
        hour = _hour_bucket(event_time)
        day = _day_bucket(event_time)

        for defn in affected_metrics:
            await AnalyticsWorker._upsert_rollup(
                db, AnalyticsHourlyRollup, record.workspace_id,
                hour, defn.metric_name.value, Decimal(1),
            )
            await AnalyticsWorker._upsert_rollup(
                db, AnalyticsDailyRollup, record.workspace_id,
                day, defn.metric_name.value, Decimal(1),
            )

    @staticmethod
    async def _upsert_rollup(db, model, workspace_id, bucket, metric_name, increment):
        """
        Upsert a rollup row. Finds existing row matching
        (workspace_id, time_bucket, metric_name) and increments,
        or creates a new one.
        """
        stmt = select(model).where(
            model.workspace_id == workspace_id,
            model.time_bucket == bucket,
            model.metric_name == metric_name,
        ).limit(1)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()

        if row:
            row.value = row.value + increment
            row.updated_at = datetime.now(timezone.utc)
        else:
            new_row = model(
                workspace_id=workspace_id,
                time_bucket=bucket,
                metric_name=metric_name,
                value=increment,
            )
            db.add(new_row)

    # ──────────────────────────────────────────────────────────
    # Full rollup recalculation from canonical events
    # ──────────────────────────────────────────────────────────
    @staticmethod
    async def rebuild_rollups(
        db: AsyncSession,
        workspace_id=None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Rebuild hourly and daily rollups from canonical analytics_events.
        Used by the backfill job and late-arrival reconciliation.
        Idempotent — produces identical results on re-run.
        """
        filters = []
        if workspace_id:
            filters.append(AnalyticsEvent.workspace_id == workspace_id)
        if start_date:
            filters.append(AnalyticsEvent.created_at >= start_date)
        if end_date:
            filters.append(AnalyticsEvent.created_at <= end_date)

        # Fetch all matching events
        stmt = select(AnalyticsEvent).where(*filters).order_by(AnalyticsEvent.created_at.asc())
        result = await db.execute(stmt)
        events = result.scalars().all()

        if not events:
            return 0

        # Build in-memory rollup buckets
        hourly_buckets = {}
        daily_buckets = {}

        for event in events:
            try:
                event_type_enum = AnalyticsEventType(event.event_type)
            except ValueError:
                continue

            affected_metrics = metric_registry.metrics_for_event(event_type_enum)
            event_time = event.created_at
            hour = _hour_bucket(event_time)
            day = _day_bucket(event_time)

            for defn in affected_metrics:
                h_key = (event.workspace_id, hour, defn.metric_name.value)
                d_key = (event.workspace_id, day, defn.metric_name.value)
                hourly_buckets[h_key] = hourly_buckets.get(h_key, Decimal(0)) + Decimal(1)
                daily_buckets[d_key] = daily_buckets.get(d_key, Decimal(0)) + Decimal(1)

        # Upsert hourly rollups
        for (ws_id, bucket, metric), value in hourly_buckets.items():
            await AnalyticsWorker._replace_rollup(db, AnalyticsHourlyRollup, ws_id, bucket, metric, value)

        # Upsert daily rollups
        for (ws_id, bucket, metric), value in daily_buckets.items():
            await AnalyticsWorker._replace_rollup(db, AnalyticsDailyRollup, ws_id, bucket, metric, value)

        await db.commit()
        return len(events)

    @staticmethod
    async def _replace_rollup(db, model, workspace_id, bucket, metric_name, value):
        """Replace (not increment) a rollup value. Used by rebuild_rollups for idempotency."""
        stmt = select(model).where(
            model.workspace_id == workspace_id,
            model.time_bucket == bucket,
            model.metric_name == metric_name,
        ).limit(1)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()

        if row:
            row.value = value
            row.updated_at = datetime.now(timezone.utc)
        else:
            new_row = model(
                workspace_id=workspace_id,
                time_bucket=bucket,
                metric_name=metric_name,
                value=value,
            )
            db.add(new_row)
