import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from backend.app.services.handoff.coordinator import HandoffCoordinator
from backend.app.schemas.handoff import AgentType, IntentType
from backend.app.models.conversation import Conversation
from backend.app.models.handoff import Handoff
from backend.app.schemas.agent import AgentResponse
from backend.app.services.handoff.state_manager import HandoffStateManager

@pytest.fixture
def mock_db():
    db = AsyncMock()
    # Ensure idempotency checks return None by default
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
async def test_sales_to_support_handoff(mock_db, base_conversation):
    with patch("backend.app.services.handoff.executor.HandoffExecutor.execute_handoff", new_callable=AsyncMock) as mock_exec:
        with patch("backend.app.agents.factory.AgentFactory.create_agent") as mock_factory:
            mock_exec.return_value = AgentResponse(content="Support here", confidence=1.0, agent_name="support")
            
            # Fix Mock: respond is async
            mock_agent = MagicMock()
            mock_agent.respond = AsyncMock(return_value=AgentResponse(content="Fallback", confidence=1.0, agent_name="sales"))
            mock_factory.return_value = mock_agent
            
            response = await HandoffCoordinator.handle_transition(
                db=mock_db,
                conversation=base_conversation,
                primary_intent=IntentType.TROUBLESHOOT.value,
                query="My product is broken",
                recent_messages=[],
                router_metadata={},
                source_message_id="msg1"
            )
            
            assert response.agent_name == "support"
            mock_exec.assert_called_once()
            args = mock_exec.call_args[1]
            assert args["decision"].to_agent == AgentType.SUPPORT
            assert args["decision"].should_handoff is True

@pytest.mark.asyncio
async def test_support_to_customer_care_handoff(mock_db, base_conversation):
    base_conversation.current_agent = AgentType.SUPPORT.value
    with patch("backend.app.services.handoff.executor.HandoffExecutor.execute_handoff", new_callable=AsyncMock) as mock_exec:
        with patch("backend.app.agents.factory.AgentFactory.create_agent") as mock_factory:
            mock_exec.return_value = AgentResponse(content="Customer Care here", confidence=1.0, agent_name="customer_care")
            
            # Fix Mock
            mock_agent = MagicMock()
            mock_agent.respond = AsyncMock(return_value=AgentResponse(content="Fallback", confidence=1.0, agent_name="support"))
            mock_factory.return_value = mock_agent
            
            response = await HandoffCoordinator.handle_transition(
                db=mock_db,
                conversation=base_conversation,
                primary_intent=IntentType.COMPLAIN.value,
                query="I want a refund, this is terrible",
                recent_messages=[],
                router_metadata={},
                source_message_id="msg2"
            )
            
            assert response.agent_name == "customer_care"
            mock_exec.assert_called_once()
            args = mock_exec.call_args[1]
            assert args["decision"].to_agent == AgentType.CUSTOMER_CARE
            assert args["decision"].should_handoff is True

@pytest.mark.asyncio
async def test_loop_prevention_cooldown(mock_db, base_conversation):
    base_conversation.handoff_count = 2
    
    # Trigger first handoff to set cooldown
    with patch("backend.app.services.handoff.executor.HandoffExecutor.execute_handoff", new_callable=AsyncMock) as mock_exec:
        with patch("backend.app.agents.factory.AgentFactory.create_agent") as mock_factory:
            mock_exec.return_value = AgentResponse(content="Support here", confidence=1.0, agent_name="support")
            
            mock_agent = MagicMock()
            mock_agent.respond = AsyncMock(return_value=AgentResponse(content="Fallback", confidence=1.0, agent_name="support"))
            mock_factory.return_value = mock_agent
            
            await HandoffCoordinator.handle_transition(
                db=mock_db,
                conversation=base_conversation,
                primary_intent=IntentType.TROUBLESHOOT.value,
                query="broken",
                recent_messages=[],
                router_metadata={},
                source_message_id="msg1"
            )
            
            # The test expects cooldown to be set. HandoffCoordinator doesn't set it, conversation_service or executor does.
            # Actually, `state_manager.update_state` might set it, but since we mock `execute_handoff`, it never runs.
            # We will manually set it here for the second half of the test to verify rule engine handles it.
            base_conversation.current_state_version = 1
            base_conversation.current_state = {
                "active_agent": "sales",
                "cooldown_until": "2050-01-01T00:00:00+00:00"
            }
        
        # Trigger second handoff while cooldown is active
        with patch("backend.app.agents.factory.AgentFactory.create_agent") as mock_factory:
            mock_agent = AsyncMock()
            mock_agent.respond.return_value = AgentResponse(content="Active agent sticking", confidence=1.0, agent_name="support")
            mock_factory.return_value = mock_agent
            
            response2 = await HandoffCoordinator.handle_transition(
                db=mock_db,
                conversation=base_conversation,
                primary_intent=IntentType.BUY_PRODUCT.value, 
                query="I want to buy",
                recent_messages=[],
                router_metadata={},
                source_message_id="msg2"
            )
            
            # Should NOT handoff, triggers loop prevention escalation
            assert response2.requires_human is True
            assert "circles" in response2.content.lower()

@pytest.mark.asyncio
async def test_idempotency_deduplication(mock_db, base_conversation):
    with patch("backend.app.services.handoff.state_manager.HandoffStateManager.check_idempotency", new_callable=AsyncMock) as mock_idem:
        mock_idem.return_value = (Handoff(), "msg1")
        
        with patch("backend.app.agents.factory.AgentFactory.create_agent") as mock_factory:
            mock_agent = AsyncMock()
            mock_agent.respond.return_value = AgentResponse(content="Cached active agent", confidence=1.0, agent_name="sales")
            mock_factory.return_value = mock_agent
            
            response = await HandoffCoordinator.handle_transition(
                db=mock_db,
                conversation=base_conversation,
                primary_intent=IntentType.TROUBLESHOOT.value,
                query="broken",
                recent_messages=[],
                router_metadata={},
                source_message_id="msg1"
            )
            
            assert response.agent_name == "sales"
