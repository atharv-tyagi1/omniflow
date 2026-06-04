"""Tests for the Smart Intent Router deterministic routing logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from backend.app.schemas.router import (
    AgentIntent,
    RouterDecision,
    RouteMessageRequest,
    IntentResult,
)
from backend.app.services.router_service import RouterService


# ---------------------------------------------------------------------------
# Mock the IntentRouter so tests are deterministic (no Gemini calls)
# ---------------------------------------------------------------------------
class MockIntentRouter:
    @staticmethod
    async def classify(message: str, history=None) -> IntentResult:
        if "pricing" in message:
            return IntentResult(primary_intent=AgentIntent.SALES, confidence=0.85)
        elif "error" in message:
            return IntentResult(primary_intent=AgentIntent.SUPPORT, confidence=0.90)
        elif "refund" in message:
            return IntentResult(primary_intent=AgentIntent.CUSTOMER_CARE, confidence=0.88)
        elif "ambiguous" in message:
            return IntentResult(primary_intent=AgentIntent.SALES, confidence=0.40)
        elif "multi" in message:
            return IntentResult(
                primary_intent=AgentIntent.SALES,
                secondary_intent=AgentIntent.SUPPORT,
                confidence=0.80,
            )
        else:
            return IntentResult(primary_intent=AgentIntent.UNKNOWN, confidence=0.95)


# Patch BEFORE any tests run
import backend.app.services.router_service as rs
rs.IntentRouter = MockIntentRouter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class MockConversation:
    def __init__(self, id, current_agent=None):
        self.id = id
        self.current_agent = current_agent


def _make_mock_db():
    """
    Build a mock AsyncSession that supports add() and flush() and execute().
    execute() returns an empty result set so HandoffRepository queries work
    without a real database.
    """
    db = AsyncMock()
    # execute returns a result whose scalars().first() is None
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    db.execute.return_value = mock_result
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_no_active_agent_high_confidence():
    db = _make_mock_db()
    conv = MockConversation(id=uuid4())
    req = RouteMessageRequest(conversation_id=conv.id, message="What is the pricing?")

    resp = await RouterService.route_message(db, req, conv)

    assert resp.decision == RouterDecision.HANDOFF
    assert resp.routed_agent == AgentIntent.SALES
    assert resp.handoff_required is True


@pytest.mark.asyncio
async def test_active_agent_retained():
    db = _make_mock_db()
    conv = MockConversation(id=uuid4(), current_agent="sales")
    req = RouteMessageRequest(conversation_id=conv.id, message="What is the pricing?")

    resp = await RouterService.route_message(db, req, conv)

    assert resp.decision == RouterDecision.STAY
    assert resp.routed_agent == AgentIntent.SALES


@pytest.mark.asyncio
async def test_strong_handoff():
    db = _make_mock_db()
    conv = MockConversation(id=uuid4(), current_agent="sales")
    req = RouteMessageRequest(
        conversation_id=conv.id, message="I am getting a 500 error."
    )

    resp = await RouterService.route_message(db, req, conv)

    assert resp.decision == RouterDecision.HANDOFF
    assert resp.routed_agent == AgentIntent.SUPPORT
    assert resp.handoff_required is True


@pytest.mark.asyncio
async def test_low_confidence_retains_agent():
    db = _make_mock_db()
    conv = MockConversation(id=uuid4(), current_agent="support")
    req = RouteMessageRequest(
        conversation_id=conv.id, message="This is very ambiguous..."
    )

    resp = await RouterService.route_message(db, req, conv)

    assert resp.decision == RouterDecision.STAY
    assert resp.routed_agent == AgentIntent.SUPPORT


@pytest.mark.asyncio
async def test_low_confidence_no_agent_clarifies():
    db = _make_mock_db()
    conv = MockConversation(id=uuid4())
    req = RouteMessageRequest(
        conversation_id=conv.id, message="This is very ambiguous..."
    )

    resp = await RouterService.route_message(db, req, conv)

    assert resp.decision == RouterDecision.CLARIFY
    assert resp.routed_agent is None


@pytest.mark.asyncio
async def test_multi_intent_ordering():
    db = _make_mock_db()
    conv = MockConversation(id=uuid4())
    req = RouteMessageRequest(conversation_id=conv.id, message="Tell me multi")

    resp = await RouterService.route_message(db, req, conv)

    assert resp.primary_intent == AgentIntent.SALES
    assert resp.secondary_intent == AgentIntent.SUPPORT
