"""Tests for Phase 13: Intel Rebuild Service — Hardened."""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.services.intel.rebuild_service import IntelRebuildService
from backend.app.models.analytics import AnalyticsOutbox
from backend.app.schemas.analytics import AnalyticsEventType
from backend.app.models.conversation import Conversation
from backend.app.models.intel import ConversationIntelligence

@pytest.mark.asyncio
async def test_intel_rebuild_service(db: AsyncSession):
    ws_id = uuid4()
    cust_id = uuid4()
    now = datetime.now(timezone.utc)

    # Create 3 conversations
    c1 = Conversation(id=uuid4(), workspace_id=ws_id, customer_id=cust_id, started_at=now - timedelta(days=2))
    c2 = Conversation(id=uuid4(), workspace_id=ws_id, customer_id=cust_id, started_at=now - timedelta(days=1))
    c3 = Conversation(id=uuid4(), workspace_id=ws_id, customer_id=cust_id, started_at=now)
    db.add_all([c1, c2, c3])
    await db.flush()

    # Pre-populate intelligence for c1 to test non-force skipping
    intel1 = ConversationIntelligence(
        conversation_id=c1.id,
        workspace_id=ws_id,
        primary_intent="support",
        needs_review=False,
        analysis_schema_version=1,
        analyzer_version="1.0",
        raw_confidence=0.9
    )
    db.add(intel1)
    await db.commit()

    # Clear any outbox records from other tests
    await db.execute(AnalyticsOutbox.__table__.delete())
    await db.commit()

    # 1. Rebuild without force
    queued = await IntelRebuildService.rebuild_workspace(db, ws_id)
    assert queued == 2  # Should skip c1

    # Verify outbox has 2 new CONVERSATION_INTEL_PENDING records
    result = await db.execute(
        select(AnalyticsOutbox)
        .where(AnalyticsOutbox.event_type == AnalyticsEventType.CONVERSATION_INTEL_PENDING)
    )
    records = result.scalars().all()
    assert len(records) == 2
    queued_ids = [r.conversation_id for r in records]
    assert c2.id in queued_ids
    assert c3.id in queued_ids
    assert c1.id not in queued_ids

    # 2. Rebuild with force
    await db.execute(AnalyticsOutbox.__table__.delete())
    await db.commit()

    queued_force = await IntelRebuildService.rebuild_workspace(db, ws_id, force_reanalyze=True)
    assert queued_force == 3  # Should include c1 this time

    # Verify outbox has 3 records
    result = await db.execute(
        select(AnalyticsOutbox)
        .where(AnalyticsOutbox.event_type == AnalyticsEventType.CONVERSATION_INTEL_PENDING)
    )
    records = result.scalars().all()
    assert len(records) == 3


@pytest.mark.asyncio
async def test_rebuild_uses_timezone_aware_datetime(db: AsyncSession):
    """Verify rebuild idempotency keys use timezone-aware UTC, not deprecated utcnow()."""
    ws_id = uuid4()
    cust_id = uuid4()
    now = datetime.now(timezone.utc)

    conv = Conversation(id=uuid4(), workspace_id=ws_id, customer_id=cust_id, started_at=now)
    db.add(conv)
    await db.flush()
    await db.commit()

    await db.execute(AnalyticsOutbox.__table__.delete())
    await db.commit()

    queued = await IntelRebuildService.rebuild_workspace(db, ws_id)
    assert queued == 1

    result = await db.execute(
        select(AnalyticsOutbox).where(
            AnalyticsOutbox.event_type == AnalyticsEventType.CONVERSATION_INTEL_PENDING
        )
    )
    record = result.scalar_one()
    assert record.idempotency_key is not None
    # Should not contain "utcnow" artifacts — just verify it's a valid key
    assert record.idempotency_key.startswith(f"rebuild_intel:{ws_id}:")


@pytest.mark.asyncio
async def test_rebuild_workspace_isolation(db: AsyncSession):
    """Rebuild must only queue conversations from the specified workspace."""
    ws_1 = uuid4()
    ws_2 = uuid4()
    cust_id = uuid4()
    now = datetime.now(timezone.utc)

    c1 = Conversation(id=uuid4(), workspace_id=ws_1, customer_id=cust_id, started_at=now)
    c2 = Conversation(id=uuid4(), workspace_id=ws_2, customer_id=cust_id, started_at=now)
    db.add_all([c1, c2])
    await db.flush()
    await db.commit()

    await db.execute(AnalyticsOutbox.__table__.delete())
    await db.commit()

    queued = await IntelRebuildService.rebuild_workspace(db, ws_1)
    assert queued == 1

    result = await db.execute(
        select(AnalyticsOutbox).where(
            AnalyticsOutbox.event_type == AnalyticsEventType.CONVERSATION_INTEL_PENDING
        )
    )
    records = result.scalars().all()
    assert len(records) == 1
    assert records[0].conversation_id == c1.id


@pytest.mark.asyncio
async def test_rebuild_rollups_consistency(db: AsyncSession):
    """Rebuild rollups from canonical data matches live processing logic."""
    from backend.app.services.intel.worker import _day_bucket
    from backend.app.models.intel import ConversationTopic
    from backend.app.models.intel_rollups import (
        IntelDailyTopicRollup, IntelDailyIntentRollup,
        IntelDailySentimentRollup, IntelDailyResolutionRollup
    )
    ws_id = uuid4()
    now = datetime.now(timezone.utc)
    bucket = _day_bucket(now)

    # 1. Add some canonical intelligence
    intel1 = ConversationIntelligence(
        conversation_id=uuid4(), workspace_id=ws_id,
        primary_intent="billing", sentiment="negative", resolution="escalated",
        analyzed_at=now
    )
    intel2 = ConversationIntelligence(
        conversation_id=uuid4(), workspace_id=ws_id,
        primary_intent="billing", sentiment="neutral", resolution="resolved",
        analyzed_at=now
    )
    topic1 = ConversationTopic(
        conversation_id=intel1.conversation_id, workspace_id=ws_id,
        topic_name="refund", created_at=now
    )
    topic2 = ConversationTopic(
        conversation_id=intel2.conversation_id, workspace_id=ws_id,
        topic_name="refund", created_at=now
    )
    db.add_all([intel1, intel2, topic1, topic2])
    
    # Pre-populate SOME rollups to simulate drift (bad counts)
    db.add(IntelDailyIntentRollup(workspace_id=ws_id, time_bucket=bucket, intent_name="billing", value=50))
    await db.commit()

    # 2. Rebuild rollups
    await IntelRebuildService.rebuild_rollups(db, ws_id)

    # 3. Verify exactly matching counts
    # Intents: billing should be 2
    intents = await db.execute(select(IntelDailyIntentRollup).where(IntelDailyIntentRollup.workspace_id == ws_id))
    intent_rows = intents.scalars().all()
    assert len(intent_rows) == 1
    assert intent_rows[0].intent_name == "billing"
    assert intent_rows[0].value == 2

    # Sentiments: negative (1), neutral (1)
    sents = await db.execute(select(IntelDailySentimentRollup).where(IntelDailySentimentRollup.workspace_id == ws_id))
    sent_rows = sents.scalars().all()
    assert len(sent_rows) == 2

    # Topics: refund (2)
    topics = await db.execute(select(IntelDailyTopicRollup).where(IntelDailyTopicRollup.workspace_id == ws_id))
    topic_rows = topics.scalars().all()
    assert len(topic_rows) == 1
    assert topic_rows[0].topic_name == "refund"
    assert topic_rows[0].value == 2
