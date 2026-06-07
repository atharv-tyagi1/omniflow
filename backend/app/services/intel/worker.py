"""Phase 13: Intel Worker — Processes conversation analysis from the outbox."""

import logging
import time as time_module
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.analytics import AnalyticsOutbox
from backend.app.schemas.analytics import AnalyticsEventType
from backend.app.models.intel import (
    ConversationIntelligence,
    ConversationIntent,
    ConversationTopic,
    ConversationSentiment,
    ConversationResolution,
    ConversationSummary
)
from backend.app.models.intel_rollups import (
    IntelDailyTopicRollup,
    IntelDailyIntentRollup,
    IntelDailySentimentRollup,
    IntelDailyResolutionRollup
)
from backend.app.services.intel.analyzer import ConversationAnalyzer
from backend.app.services.intel.topic_registry import TopicRegistryService

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
BATCH_SIZE = 100


def _day_bucket(dt: datetime) -> datetime:
    """Truncate to UTC day boundary, normalizing timezone first."""
    utc_dt = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return utc_dt.replace(hour=0, minute=0, second=0, microsecond=0)


class IntelWorker:
    """Consumes `conversation_intel_pending` events from the shared outbox."""

    @staticmethod
    async def process_outbox_batch(db: AsyncSession, batch_size: int = BATCH_SIZE) -> int:
        """
        Process up to `batch_size` pending intel outbox records.
        """
        start_time = time_module.time()

        stmt = (
            select(AnalyticsOutbox)
            .where(
                AnalyticsOutbox.status == "pending",
                AnalyticsOutbox.attempts < MAX_ATTEMPTS,
                AnalyticsOutbox.event_type == AnalyticsEventType.CONVERSATION_INTEL_PENDING
            )
            .order_by(AnalyticsOutbox.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await db.execute(stmt)
        records = result.scalars().all()

        if not records:
            return 0

        # Operational metric: queue depth and lag
        now = datetime.now(timezone.utc)
        oldest_created = records[0].created_at
        if oldest_created.tzinfo is None:
            oldest_created = oldest_created.replace(tzinfo=timezone.utc)
        lag_seconds = int((now - oldest_created).total_seconds())

        logger.info(
            "Operational Metric: Intel batch started",
            extra={
                "metric_name": "intel_batch_started",
                "intel_queue_depth_batch": len(records),
                "intel_worker_lag_seconds": lag_seconds,
            }
        )

        processed = 0
        failed = 0
        skipped = 0

        for record in records:
            try:
                # Idempotency check: see if intelligence already exists
                # Uses workspace_id + conversation_id for multi-tenant safety
                existing = await db.execute(
                    select(ConversationIntelligence.id).where(
                        ConversationIntelligence.conversation_id == record.conversation_id,
                        ConversationIntelligence.workspace_id == record.workspace_id,
                    ).limit(1)
                )
                if existing.scalar_one_or_none() is not None:
                    # Already processed — idempotent skip
                    record.status = "processed"
                    record.processed_at = now
                    skipped += 1
                    processed += 1
                    continue

                # Run Analysis
                analysis_data = await ConversationAnalyzer.analyze_conversation(
                    db, record.conversation_id, record.workspace_id
                )
                if analysis_data is None:
                    # Genuinely empty conversation — no messages to analyze
                    record.status = "processed"
                    record.processed_at = now
                    processed += 1
                    continue

                await IntelWorker._persist_intelligence(db, record, analysis_data, now)
                
                record.status = "processed"
                record.processed_at = now
                processed += 1

                logger.info(
                    "Operational Metric: Intel generated",
                    extra={
                        "metric_name": "intel_generation_success",
                        "conversation_id": str(record.conversation_id),
                        "workspace_id": str(record.workspace_id),
                    }
                )

            except Exception as exc:
                record.attempts += 1
                record.last_error = str(exc)[:500]
                failed += 1
                if record.attempts >= MAX_ATTEMPTS:
                    record.status = "failed"
                    logger.error(
                        "Operational Metric: Intel permanently failed",
                        extra={
                            "metric_name": "intel_generation_failed",
                            "conversation_id": str(record.conversation_id),
                            "workspace_id": str(record.workspace_id),
                            "error": exc.__class__.__name__,
                            "attempts": record.attempts,
                        }
                    )
                else:
                    logger.warning(
                        f"Intel outbox record {record.id} attempt {record.attempts} failed: {exc}",
                        extra={
                            "metric_name": "intel_generation_retried",
                            "conversation_id": str(record.conversation_id),
                            "attempts": record.attempts,
                        }
                    )

        await db.commit()

        # Clear topic cache after batch to keep memory bounded
        TopicRegistryService.clear_cache()

        duration_ms = int((time_module.time() - start_time) * 1000)
        logger.info(
            "Operational Metric: Intel batch completed",
            extra={
                "metric_name": "intel_batch_completed",
                "duration_ms": duration_ms,
                "processed_count": processed,
                "failed_count": failed,
                "skipped_count": skipped,
            }
        )
        return processed

    @staticmethod
    async def _persist_intelligence(
        db: AsyncSession,
        record: AnalyticsOutbox,
        data: dict,
        now: datetime
    ) -> None:
        """Write analyzed data to intelligence models and update rollups."""
        
        ws_id = record.workspace_id
        conv_id = record.conversation_id
        schema_version = ConversationAnalyzer.SCHEMA_VERSION
        analyzer_version = ConversationAnalyzer.ANALYZER_VERSION

        needs_review = data.get("needs_review", False)
        confidence = Decimal(str(data.get("confidence_score", 0.0)))
        review_reason = data.get("review_reason")

        primary_intent = data.get("primary_intent")
        sentiment = data.get("sentiment")
        resolution = data.get("resolution")

        # 1. Canonical Root Entity
        root_intel = ConversationIntelligence(
            workspace_id=ws_id,
            conversation_id=conv_id,
            primary_intent=primary_intent,
            sentiment=sentiment,
            resolution=resolution,
            needs_review=needs_review,
            raw_confidence=confidence,
            review_reason=review_reason,
            analysis_schema_version=schema_version,
            analyzer_version=analyzer_version,
            analyzed_at=now
        )
        db.add(root_intel)

        # 2. Conversation Intent
        sec_intents = data.get("secondary_intents", [])
        if primary_intent:
            intent_entity = ConversationIntent(
                workspace_id=ws_id,
                conversation_id=conv_id,
                primary_intent=primary_intent,
                secondary_intents=sec_intents,
                confidence=confidence,
                analysis_schema_version=schema_version,
                analyzer_version=analyzer_version
            )
            db.add(intent_entity)
            await IntelWorker._upsert_rollup(db, IntelDailyIntentRollup, ws_id, now, "intent_name", primary_intent)

        # 3. Sentiment
        if sentiment:
            sentiment_entity = ConversationSentiment(
                workspace_id=ws_id,
                conversation_id=conv_id,
                sentiment=sentiment,
                confidence=confidence,
                needs_review=needs_review,
                analysis_schema_version=schema_version,
                analyzer_version=analyzer_version,
                analyzed_at=now
            )
            db.add(sentiment_entity)
            await IntelWorker._upsert_rollup(db, IntelDailySentimentRollup, ws_id, now, "sentiment", sentiment)

        # 4. Resolution
        if resolution:
            resolution_entity = ConversationResolution(
                workspace_id=ws_id,
                conversation_id=conv_id,
                resolution_type=resolution,
                confidence=confidence,
                needs_review=needs_review,
                analysis_schema_version=schema_version,
                analyzer_version=analyzer_version,
                analyzed_at=now
            )
            db.add(resolution_entity)
            await IntelWorker._upsert_rollup(db, IntelDailyResolutionRollup, ws_id, now, "resolution_type", resolution)

        # 5. Topics
        topics = data.get("topics", [])
        canonical_topics = await TopicRegistryService.normalize_topics(db, ws_id, topics)
        for topic in canonical_topics:
            topic_entity = ConversationTopic(
                workspace_id=ws_id,
                conversation_id=conv_id,
                topic_name=topic,
                confidence=confidence,
                needs_review=needs_review,
                analysis_schema_version=schema_version,
                analyzer_version=analyzer_version
            )
            db.add(topic_entity)
            await IntelWorker._upsert_rollup(db, IntelDailyTopicRollup, ws_id, now, "topic_name", topic)

        # 6. Summary
        short_summary = data.get("short_summary")
        if short_summary:
            summary_entity = ConversationSummary(
                workspace_id=ws_id,
                conversation_id=conv_id,
                short_summary=short_summary,
                long_summary=data.get("long_summary"),
                analysis_schema_version=schema_version,
                analyzer_version=analyzer_version
            )
            db.add(summary_entity)

    @staticmethod
    async def _upsert_rollup(db: AsyncSession, model, workspace_id, event_time, key_field, key_value, increment=Decimal(1)):
        """Upsert an intel daily rollup row. Concurrency-safe via IntegrityError retry."""
        bucket = _day_bucket(event_time)
        stmt = select(model).where(
            model.workspace_id == workspace_id,
            model.time_bucket == bucket,
            getattr(model, key_field) == key_value
        ).limit(1)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()

        if row:
            row.value = row.value + increment
            row.updated_at = datetime.now(timezone.utc)
        else:
            try:
                new_row = model(
                    workspace_id=workspace_id,
                    time_bucket=bucket,
                    value=increment
                )
                setattr(new_row, key_field, key_value)
                db.add(new_row)
                await db.flush()
            except IntegrityError:
                # Concurrent insert beat us — re-fetch and increment
                await db.rollback()
                result = await db.execute(stmt)
                row = result.scalar_one_or_none()
                if row:
                    row.value = row.value + increment
                    row.updated_at = datetime.now(timezone.utc)
                else:
                    # Should not happen, but log defensively
                    logger.error(
                        f"Rollup upsert failed: IntegrityError but row not found on retry "
                        f"for {model.__tablename__} ws={workspace_id} key={key_value}"
                    )
