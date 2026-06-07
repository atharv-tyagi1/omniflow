import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from backend.app.services.handoff.coordinator import HandoffCoordinator
from backend.app.schemas.handoff import AgentType, IntentType, ConversationHandoffStateV1
from backend.app.models.conversation import Conversation
from backend.app.schemas.agent import AgentResponse

@pytest.fixture
def mock_db():
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result
    return db

@pytest.fixture
def base_conversation():
    return Conversation(
        id=uuid4(),
        workspace_id=uuid4(),
        customer_id=uuid4(),
        current_agent=AgentType.SALES.value,
        handoff_count=0
    )

@pytest.mark.asyncio
async def test_ping_pong_oscillation(mock_db, base_conversation):
    # Setup conversation state to simulate oscillating
    base_conversation.current_agent = AgentType.SALES.value
    state = ConversationHandoffStateV1(
        active_agent=AgentType.SALES,
        previous_agent=AgentType.SUPPORT
    )
    base_conversation.current_state = state.model_dump()
    base_conversation.current_state_version = 1
    
    with patch("backend.app.agents.factory.AgentFactory.create_agent") as mock_factory:
        mock_agent = AsyncMock()
        mock_agent.respond.return_value = AgentResponse(content="Sales sticking", confidence=1.0, agent_name="sales")
        mock_factory.return_value = mock_agent
        
        response = await HandoffCoordinator.handle_transition(
            db=mock_db,
            conversation=base_conversation,
            primary_intent=IntentType.TROUBLESHOOT.value, # Normally would go to Support
            query="help me",
            recent_messages=[],
            router_metadata={},
            source_message_id="msg_ping_pong"
        )
        
        # Rule engine should block the oscillation and escalate
        assert response.requires_human is True
        assert "circles" in response.content.lower()

@pytest.mark.asyncio
async def test_transactional_rollback(mock_db, base_conversation):
    # Setup
    base_conversation.current_agent = AgentType.SALES.value
    
    from sqlalchemy.exc import SQLAlchemyError
    mock_db.commit.side_effect = [None, SQLAlchemyError("DB constraint violation"), None]
    
    with patch("backend.app.services.handoff.executor.AgentFactory.create_agent") as mock_factory:
        mock_agent = AsyncMock()
        mock_agent.respond.return_value = AgentResponse(content="Will be rolled back", confidence=1.0, agent_name="support")
        mock_factory.return_value = mock_agent
        
        # Test direct executor since that's where the rollback lives
        from backend.app.services.handoff.executor import HandoffExecutor
        from backend.app.models.handoff import Handoff
        from backend.app.schemas.handoff import HandoffDecision, HandoffReason
        
        decision = HandoffDecision(should_handoff=True, to_agent=AgentType.SUPPORT, reason=HandoffReason.TECHNICAL_ISSUE)
        handoff_record = Handoff(from_agent="sales", to_agent="support")
        
        response = await HandoffExecutor.execute_handoff(
            db=mock_db,
            conversation=base_conversation,
            decision=decision,
            source_message_id="msg_txn",
            query="help me",
            bounded_context={},
            router_metadata={}
        )
        
        assert response.requires_human is True
        assert mock_db.rollback.called is True
