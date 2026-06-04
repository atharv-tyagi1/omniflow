import pytest
from uuid import uuid4

from backend.app.schemas.router import (
    AgentIntent,
    RouterDecision,
    RouteMessageRequest,
)
from backend.app.services.router_service import RouterService
from backend.app.schemas.router import IntentResult


# Mocking the AI dependency for deterministic test conditions
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
                confidence=0.80
            )
        else:
            return IntentResult(primary_intent=AgentIntent.UNKNOWN, confidence=0.95)

# Patch the underlying dependency
import backend.app.services.router_service as rs
rs.IntentRouter = MockIntentRouter


class MockConversation:
    def __init__(self, id, current_agent=None):
        self.id = id
        self.current_agent = current_agent


class MockDB:
    def __init__(self):
        self.agent_updates = []
        self.handoffs = []
        
    def add(self, obj):
        if hasattr(obj, "to_agent"):
            self.handoffs.append(obj)
        else:
            self.agent_updates.append(obj)

    async def flush(self):
        pass


@pytest.mark.asyncio
async def test_no_active_agent_high_confidence():
    db = MockDB()
    conv = MockConversation(id=uuid4())
    req = RouteMessageRequest(conversation_id=conv.id, message="What is the pricing?")
    
    resp = await RouterService.route_message(db, req, conv)
    
    assert resp.decision == RouterDecision.STAY
    assert resp.routed_agent == AgentIntent.SALES
    assert resp.handoff_required is False


@pytest.mark.asyncio
async def test_active_agent_retained():
    db = MockDB()
    conv = MockConversation(id=uuid4(), current_agent="sales")
    req = RouteMessageRequest(conversation_id=conv.id, message="What is the pricing?")
    
    resp = await RouterService.route_message(db, req, conv)
    
    assert resp.decision == RouterDecision.STAY
    assert resp.routed_agent == AgentIntent.SALES


@pytest.mark.asyncio
async def test_strong_handoff():
    db = MockDB()
    conv = MockConversation(id=uuid4(), current_agent="sales")
    req = RouteMessageRequest(conversation_id=conv.id, message="I am getting a 500 error.")
    
    resp = await RouterService.route_message(db, req, conv)
    
    assert resp.decision == RouterDecision.HANDOFF
    assert resp.routed_agent == AgentIntent.SUPPORT
    assert resp.handoff_required is True


@pytest.mark.asyncio
async def test_low_confidence_retains_agent():
    db = MockDB()
    conv = MockConversation(id=uuid4(), current_agent="support")
    req = RouteMessageRequest(conversation_id=conv.id, message="This is very ambiguous...")
    
    resp = await RouterService.route_message(db, req, conv)
    
    assert resp.decision == RouterDecision.STAY
    assert resp.routed_agent == AgentIntent.SUPPORT


@pytest.mark.asyncio
async def test_low_confidence_no_agent_clarifies():
    db = MockDB()
    conv = MockConversation(id=uuid4())
    req = RouteMessageRequest(conversation_id=conv.id, message="This is very ambiguous...")
    
    resp = await RouterService.route_message(db, req, conv)
    
    assert resp.decision == RouterDecision.CLARIFY
    assert resp.routed_agent is None


@pytest.mark.asyncio
async def test_multi_intent_ordering():
    db = MockDB()
    conv = MockConversation(id=uuid4())
    req = RouteMessageRequest(conversation_id=conv.id, message="Tell me multi")
    
    resp = await RouterService.route_message(db, req, conv)
    
    assert resp.primary_intent == AgentIntent.SALES
    assert resp.secondary_intent == AgentIntent.SUPPORT
