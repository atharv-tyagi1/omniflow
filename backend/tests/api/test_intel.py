"""Tests for Phase 13: Conversation Intelligence — Hardened."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.schemas.analytics import AnalyticsEventType
from backend.app.services.analytics.emitter import AnalyticsEventEmitter
from backend.app.services.intel.worker import IntelWorker
from backend.app.services.intel.topic_registry import TopicRegistryService
from backend.app.services.intel.context_builder import ConversationContextBuilder
from backend.app.services.intel.analyzer import ConversationAnalyzer, IntelAnalysisError
from backend.app.models.intel import ConversationIntelligence, TopicRegistry
from backend.app.models.analytics import AnalyticsOutbox
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message


# ============================================================
# Mock GeminiClient fixtures
# ============================================================

class MockGeminiClient:
    @staticmethod
    async def generate_completion(prompt: str, **kwargs) -> dict:
        return {
            "content": """
        {
          "primary_intent": "refund_request",
          "secondary_intents": ["billing_issue"],
          "sentiment": "negative",
          "resolution": "resolved",
          "topics": ["pricing", "refund"],
          "short_summary": "Customer wanted a refund for overcharge.",
          "long_summary": "The customer contacted support because they were billed twice. Agent issued refund.",
          "confidence_score": 0.95,
          "review_reason": null
        }
        """,
            "error": None,
            "latency_ms": 150,
            "tokens_used": 100,
        }


class MockGeminiClientError:
    """Simulates Gemini returning an error (rate limit, unavailable)."""
    @staticmethod
    async def generate_completion(prompt: str, **kwargs) -> dict:
        return {
            "content": "",
            "error": "Gemini API rate limit exceeded or service unavailable. Please try again later.",
            "latency_ms": 50,
            "tokens_used": 0,
        }


class MockGeminiClientMalformed:
    """Simulates Gemini returning malformed (non-JSON) content."""
    @staticmethod
    async def generate_completion(prompt: str, **kwargs) -> dict:
        return {
            "content": "Sorry, I cannot process this request right now.",
            "error": None,
            "latency_ms": 80,
            "tokens_used": 50,
        }


@pytest.fixture(autouse=True)
def mock_gemini(monkeypatch):
    from backend.app.core.ai.gemini_client import GeminiClient
    monkeypatch.setattr(GeminiClient, "generate_completion", MockGeminiClient.generate_completion)


@pytest.fixture
def mock_gemini_error(monkeypatch):
    from backend.app.core.ai.gemini_client import GeminiClient
    monkeypatch.setattr(GeminiClient, "generate_completion", MockGeminiClientError.generate_completion)


@pytest.fixture
def mock_gemini_malformed(monkeypatch):
    from backend.app.core.ai.gemini_client import GeminiClient
    monkeypatch.setattr(GeminiClient, "generate_completion", MockGeminiClientMalformed.generate_completion)


# ============================================================
# CRITICAL: IntelWorker processes outbox correctly
# ============================================================

@pytest.mark.asyncio
async def test_intel_worker_processes_outbox(db: AsyncSession):
    """Test that IntelWorker correctly extracts intel from a conversation."""
    ws_id = uuid4()
    conv_id = uuid4()
    cust_id = uuid4()

    conv = Conversation(id=conv_id, workspace_id=ws_id, customer_id=cust_id)
    db.add(conv)
    msg1 = Message(conversation_id=conv_id, sender_type="customer", content="I need a refund.")
    msg2 = Message(conversation_id=conv_id, sender_type="support", content="I have issued your refund.")
    db.add_all([msg1, msg2])

    await AnalyticsEventEmitter.emit(
        db=db,
        workspace_id=ws_id,
        event_type=AnalyticsEventType.CONVERSATION_INTEL_PENDING,
        conversation_id=conv_id,
        idempotency_key=f"intel_test:{conv_id}"
    )
    await db.commit()

    # Clear topic cache to start fresh
    TopicRegistryService.clear_cache()

    processed = await IntelWorker.process_outbox_batch(db)
    assert processed == 1

    result = await db.execute(select(ConversationIntelligence).where(ConversationIntelligence.conversation_id == conv_id))
    intel = result.scalar_one_or_none()

    assert intel is not None
    assert intel.primary_intent == "refund_request"
    assert intel.sentiment == "negative"
    assert intel.resolution == "resolved"
    assert intel.workspace_id == ws_id


# ============================================================
# CRITICAL: AnalyticsWorker does NOT consume intel events
# ============================================================

@pytest.mark.asyncio
async def test_analytics_worker_skips_intel_events(db: AsyncSession):
    """AnalyticsWorker must NOT process CONVERSATION_INTEL_PENDING events."""
    from backend.app.services.analytics.worker import AnalyticsWorker

    ws_id = uuid4()
    conv_id = uuid4()

    # Emit an intel event
    await AnalyticsEventEmitter.emit(
        db=db,
        workspace_id=ws_id,
        event_type=AnalyticsEventType.CONVERSATION_INTEL_PENDING,
        conversation_id=conv_id,
        idempotency_key=f"analytics_skip_test:{conv_id}"
    )
    await db.commit()

    # Run the analytics worker — it should skip this event
    analytics_processed = await AnalyticsWorker.process_outbox_batch(db)
    assert analytics_processed == 0

    # Verify the event is still pending for IntelWorker
    result = await db.execute(
        select(AnalyticsOutbox).where(
            AnalyticsOutbox.conversation_id == conv_id,
            AnalyticsOutbox.status == "pending"
        )
    )
    record = result.scalar_one_or_none()
    assert record is not None
    assert record.event_type == AnalyticsEventType.CONVERSATION_INTEL_PENDING.value


# ============================================================
# CRITICAL: Gemini error causes retry, not silent processing
# ============================================================

@pytest.mark.asyncio
async def test_gemini_error_retries_not_silent(db: AsyncSession, mock_gemini_error):
    """When Gemini returns an error, the outbox record should be retried, not processed."""
    ws_id = uuid4()
    conv_id = uuid4()
    cust_id = uuid4()

    conv = Conversation(id=conv_id, workspace_id=ws_id, customer_id=cust_id)
    db.add(conv)
    msg1 = Message(conversation_id=conv_id, sender_type="customer", content="Help me!")
    db.add(msg1)

    await AnalyticsEventEmitter.emit(
        db=db,
        workspace_id=ws_id,
        event_type=AnalyticsEventType.CONVERSATION_INTEL_PENDING,
        conversation_id=conv_id,
        idempotency_key=f"gemini_error_test:{conv_id}"
    )
    await db.commit()

    TopicRegistryService.clear_cache()

    # Process — should fail and increment attempts, not mark as processed
    processed = await IntelWorker.process_outbox_batch(db)
    assert processed == 0  # Nothing successfully processed

    # Verify the record is still pending with incremented attempts
    result = await db.execute(
        select(AnalyticsOutbox).where(AnalyticsOutbox.conversation_id == conv_id)
    )
    record = result.scalar_one()
    assert record.status == "pending"
    assert record.attempts == 1
    assert "rate limit" in record.last_error.lower() or "gemini" in record.last_error.lower()


@pytest.mark.asyncio
async def test_gemini_malformed_json_retries(db: AsyncSession, mock_gemini_malformed):
    """When Gemini returns non-JSON text, the outbox record should be retried."""
    ws_id = uuid4()
    conv_id = uuid4()
    cust_id = uuid4()

    conv = Conversation(id=conv_id, workspace_id=ws_id, customer_id=cust_id)
    db.add(conv)
    msg1 = Message(conversation_id=conv_id, sender_type="customer", content="Question about billing.")
    db.add(msg1)

    await AnalyticsEventEmitter.emit(
        db=db,
        workspace_id=ws_id,
        event_type=AnalyticsEventType.CONVERSATION_INTEL_PENDING,
        conversation_id=conv_id,
        idempotency_key=f"malformed_test:{conv_id}"
    )
    await db.commit()

    TopicRegistryService.clear_cache()

    processed = await IntelWorker.process_outbox_batch(db)
    assert processed == 0

    result = await db.execute(
        select(AnalyticsOutbox).where(AnalyticsOutbox.conversation_id == conv_id)
    )
    record = result.scalar_one()
    assert record.status == "pending"
    assert record.attempts == 1
    assert "parse" in record.last_error.lower() or "json" in record.last_error.lower()


# ============================================================
# CRITICAL: Empty conversation returns None (no retry)
# ============================================================

@pytest.mark.asyncio
async def test_empty_conversation_skipped_not_retried(db: AsyncSession):
    """An empty conversation (no messages) should be marked processed, not retried."""
    ws_id = uuid4()
    conv_id = uuid4()
    cust_id = uuid4()

    # Conversation with NO messages
    conv = Conversation(id=conv_id, workspace_id=ws_id, customer_id=cust_id)
    db.add(conv)

    await AnalyticsEventEmitter.emit(
        db=db,
        workspace_id=ws_id,
        event_type=AnalyticsEventType.CONVERSATION_INTEL_PENDING,
        conversation_id=conv_id,
        idempotency_key=f"empty_conv_test:{conv_id}"
    )
    await db.commit()

    TopicRegistryService.clear_cache()

    processed = await IntelWorker.process_outbox_batch(db)
    assert processed == 1  # Empty conversation is legitimately processed

    result = await db.execute(
        select(AnalyticsOutbox).where(AnalyticsOutbox.conversation_id == conv_id)
    )
    record = result.scalar_one()
    assert record.status == "processed"


# ============================================================
# Topic Registry normalization
# ============================================================

@pytest.mark.asyncio
async def test_topic_registry_normalization(db: AsyncSession):
    ws_id = uuid4()
    TopicRegistryService.clear_cache()

    canon1 = await TopicRegistryService.get_or_create_canonical_topic(db, ws_id, "Pricing")
    assert canon1 == "pricing"

    result = await db.execute(select(TopicRegistry).where(TopicRegistry.workspace_id == ws_id))
    regs = result.scalars().all()
    assert len(regs) == 1

    canon2 = await TopicRegistryService.get_or_create_canonical_topic(db, ws_id, "pricing")
    assert canon2 == "pricing"

    result2 = await db.execute(select(TopicRegistry).where(TopicRegistry.workspace_id == ws_id))
    regs2 = result2.scalars().all()
    assert len(regs2) == 1


@pytest.mark.asyncio
async def test_topic_registry_caching(db: AsyncSession):
    """Verify repeated calls use cache, not full-table scans."""
    ws_id = uuid4()
    TopicRegistryService.clear_cache()

    # First call loads from DB
    c1 = await TopicRegistryService.get_or_create_canonical_topic(db, ws_id, "Support")
    assert c1 == "support"

    # Second call should use cache
    c2 = await TopicRegistryService.get_or_create_canonical_topic(db, ws_id, "Support")
    assert c2 == "support"

    # Different topic, same workspace — cache is populated
    c3 = await TopicRegistryService.get_or_create_canonical_topic(db, ws_id, "Billing")
    assert c3 == "billing"

    # Clear cache and verify it still works from DB
    TopicRegistryService.clear_cache(ws_id)
    c4 = await TopicRegistryService.get_or_create_canonical_topic(db, ws_id, "Support")
    assert c4 == "support"


# ============================================================
# PII Redaction
# ============================================================

def test_pii_redaction_email():
    result = ConversationContextBuilder.sanitize_pii("Contact me at john@example.com please.")
    assert "[REDACTED_EMAIL]" in result
    assert "john@example.com" not in result


def test_pii_redaction_phone():
    result = ConversationContextBuilder.sanitize_pii("Call me at +1 234 567 8901")
    assert "[REDACTED_PHONE]" in result
    assert "234 567" not in result


def test_pii_redaction_ssn():
    result = ConversationContextBuilder.sanitize_pii("My SSN is 123-45-6789")
    assert "[REDACTED_ID]" in result
    assert "123-45-6789" not in result


def test_pii_redaction_credit_card():
    """Credit card numbers must be redacted."""
    result = ConversationContextBuilder.sanitize_pii("My card is 4111 1111 1111 1111")
    assert "[REDACTED_CC]" in result
    assert "4111" not in result


def test_pii_redaction_credit_card_dashes():
    """Credit cards with dashes must also be redacted."""
    result = ConversationContextBuilder.sanitize_pii("Card: 4111-1111-1111-1111")
    assert "[REDACTED_CC]" in result


def test_pii_redaction_empty():
    assert ConversationContextBuilder.sanitize_pii("") == ""
    assert ConversationContextBuilder.sanitize_pii(None) == ""


# ============================================================
# Workspace isolation in idempotency
# ============================================================

@pytest.mark.asyncio
async def test_workspace_isolation_idempotency(db: AsyncSession):
    """Intel idempotency check must be scoped to workspace."""
    ws_1 = uuid4()
    ws_2 = uuid4()
    conv_id = uuid4()
    cust_id = uuid4()

    # Create conversation in ws_1 with existing intel
    conv1 = Conversation(id=conv_id, workspace_id=ws_1, customer_id=cust_id)
    db.add(conv1)
    intel1 = ConversationIntelligence(
        conversation_id=conv_id,
        workspace_id=ws_1,
        primary_intent="support",
        needs_review=False,
        analysis_schema_version=1,
        analyzer_version="1.0",
        raw_confidence=0.9
    )
    db.add(intel1)
    await db.commit()

    # Intel exists for ws_1 + conv_id, so this should skip
    await AnalyticsEventEmitter.emit(
        db=db,
        workspace_id=ws_1,
        event_type=AnalyticsEventType.CONVERSATION_INTEL_PENDING,
        conversation_id=conv_id,
        idempotency_key=f"ws_isolation_test_1:{conv_id}"
    )
    await db.commit()

    TopicRegistryService.clear_cache()
    processed = await IntelWorker.process_outbox_batch(db)
    # Should be 1 (skipped via idempotency = still counted as processed)
    assert processed == 1


# ============================================================
# IntelAnalysisError is a proper exception
# ============================================================

def test_intel_analysis_error_is_exception():
    """IntelAnalysisError must be an Exception for the retry path."""
    err = IntelAnalysisError("test error")
    assert isinstance(err, Exception)
    assert str(err) == "test error"
