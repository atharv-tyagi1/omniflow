"""Phase 13: Intel Rebuild Service."""

import logging
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.analytics import AnalyticsEventType
from backend.app.services.analytics.emitter import AnalyticsEventEmitter
from backend.app.models.conversation import Conversation
from backend.app.models.intel import ConversationIntelligence

logger = logging.getLogger(__name__)

# Chunk size for memory-safe rebuild of large workspaces
REBUILD_CHUNK_SIZE = 500


class IntelRebuildService:
    """Service to enqueue idempotent rebuilds of conversation intelligence."""

    @staticmethod
    async def rebuild_workspace(
        db: AsyncSession,
        workspace_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        force_reanalyze: bool = False
    ) -> int:
        """
        Enqueues intelligence analysis for conversations in a workspace.
        Processes in chunks to avoid loading all conversation IDs into memory.
        """
        filters = [Conversation.workspace_id == workspace_id]
        if start_date:
            filters.append(Conversation.started_at >= start_date)
        if end_date:
            filters.append(Conversation.started_at <= end_date)

        # Count total for progress logging
        count_stmt = select(func.count(Conversation.id)).where(*filters)
        total_result = await db.execute(count_stmt)
        total_conversations = total_result.scalar() or 0

        if total_conversations == 0:
            return 0

        logger.info(
            "Intel rebuild started",
            extra={
                "metric_name": "intel_rebuild_started",
                "workspace_id": str(workspace_id),
                "total_conversations": total_conversations,
                "force_reanalyze": force_reanalyze,
            }
        )

        queued = 0
        offset = 0

        while offset < total_conversations:
            # Chunked query — bounded memory usage
            chunk_stmt = (
                select(Conversation.id)
                .where(*filters)
                .order_by(Conversation.started_at.asc())
                .limit(REBUILD_CHUNK_SIZE)
                .offset(offset)
            )
            result = await db.execute(chunk_stmt)
            conversation_ids = result.scalars().all()

            if not conversation_ids:
                break

            for conv_id in conversation_ids:
                if not force_reanalyze:
                    existing_stmt = select(ConversationIntelligence.id).where(
                        ConversationIntelligence.conversation_id == conv_id,
                        ConversationIntelligence.workspace_id == workspace_id,
                    ).limit(1)
                    existing = await db.execute(existing_stmt)
                    if existing.scalar_one_or_none() is not None:
                        continue

                await AnalyticsEventEmitter.emit(
                    db=db,
                    workspace_id=workspace_id,
                    event_type=AnalyticsEventType.CONVERSATION_INTEL_PENDING,
                    conversation_id=conv_id,
                    idempotency_key=f"rebuild_intel:{workspace_id}:{conv_id}:{datetime.now(timezone.utc).timestamp()}"
                )
                queued += 1

            offset += REBUILD_CHUNK_SIZE

            # Progress logging
            logger.info(
                "Intel rebuild progress",
                extra={
                    "metric_name": "intel_rebuild_progress",
                    "workspace_id": str(workspace_id),
                    "queued_so_far": queued,
                    "offset": offset,
                    "total_conversations": total_conversations,
                }
            )

        await db.commit()

        logger.info(
            "Intel rebuild completed",
            extra={
                "metric_name": "intel_rebuild_completed",
                "workspace_id": str(workspace_id),
                "total_queued": queued,
                "total_conversations": total_conversations,
            }
        )
        return queued

    @staticmethod
    async def rebuild_rollups(db: AsyncSession, workspace_id: UUID) -> None:
        """
        Rebuilds all daily rollups strictly from the canonical intelligence tables.
        This fixes any drift caused by duplicate events or schema migrations.
        """
        from sqlalchemy import delete
        from backend.app.models.intel_rollups import (
            IntelDailyTopicRollup, IntelDailyIntentRollup,
            IntelDailySentimentRollup, IntelDailyResolutionRollup
        )
        from backend.app.models.intel import ConversationIntelligence, ConversationTopic
        from backend.app.services.intel.worker import _day_bucket
        
        # 1. Clear existing rollups
        await db.execute(delete(IntelDailyTopicRollup).where(IntelDailyTopicRollup.workspace_id == workspace_id))
        await db.execute(delete(IntelDailyIntentRollup).where(IntelDailyIntentRollup.workspace_id == workspace_id))
        await db.execute(delete(IntelDailySentimentRollup).where(IntelDailySentimentRollup.workspace_id == workspace_id))
        await db.execute(delete(IntelDailyResolutionRollup).where(IntelDailyResolutionRollup.workspace_id == workspace_id))
        await db.flush()
        
        # 2. Rebuild Intents, Sentiments, Resolutions from ConversationIntelligence
        offset = 0
        chunk_size = 1000
        
        intent_counts = {}
        sentiment_counts = {}
        resolution_counts = {}
        
        while True:
            stmt = select(ConversationIntelligence).where(
                ConversationIntelligence.workspace_id == workspace_id
            ).limit(chunk_size).offset(offset)
            result = await db.execute(stmt)
            intels = result.scalars().all()
            if not intels:
                break
                
            for intel in intels:
                bucket = _day_bucket(intel.analyzed_at)
                if intel.primary_intent:
                    key = (bucket, intel.primary_intent)
                    intent_counts[key] = intent_counts.get(key, 0) + 1
                if intel.sentiment:
                    key = (bucket, intel.sentiment)
                    sentiment_counts[key] = sentiment_counts.get(key, 0) + 1
                if intel.resolution:
                    key = (bucket, intel.resolution)
                    resolution_counts[key] = resolution_counts.get(key, 0) + 1
            
            offset += chunk_size
            
        # 3. Rebuild Topics from ConversationTopic
        offset = 0
        topic_counts = {}
        while True:
            stmt = select(ConversationTopic).where(
                ConversationTopic.workspace_id == workspace_id
            ).limit(chunk_size).offset(offset)
            result = await db.execute(stmt)
            topics = result.scalars().all()
            if not topics:
                break
                
            for topic in topics:
                dt = topic.created_at or datetime.now(timezone.utc)
                bucket = _day_bucket(dt)
                key = (bucket, topic.topic_name)
                topic_counts[key] = topic_counts.get(key, 0) + 1
                
            offset += chunk_size
            
        # 4. Insert new rollups
        for (bucket, intent), count in intent_counts.items():
            db.add(IntelDailyIntentRollup(workspace_id=workspace_id, time_bucket=bucket, intent_name=intent, value=count))
            
        for (bucket, sentiment), count in sentiment_counts.items():
            db.add(IntelDailySentimentRollup(workspace_id=workspace_id, time_bucket=bucket, sentiment=sentiment, value=count))
            
        for (bucket, res), count in resolution_counts.items():
            db.add(IntelDailyResolutionRollup(workspace_id=workspace_id, time_bucket=bucket, resolution_type=res, value=count))
            
        for (bucket, topic), count in topic_counts.items():
            db.add(IntelDailyTopicRollup(workspace_id=workspace_id, time_bucket=bucket, topic_name=topic, value=count))
            
        await db.commit()
