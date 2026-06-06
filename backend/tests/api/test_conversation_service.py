import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.conversation_service import ConversationService
from backend.app.schemas.router import RouterDecision, AgentIntent, RouteMessageResponse
from backend.app.schemas.agent import AgentResponse, AgentType


@pytest.fixture
def mock_router_sales():
    with patch("backend.app.services.conversation_service.RouterService.route_message", new_callable=AsyncMock) as mock:
        mock.return_value = RouteMessageResponse(
            decision=RouterDecision.HANDOFF,
            primary_intent=AgentIntent.SALES,
            routed_agent=AgentIntent.SALES,
            confidence=0.9,
            handoff_required=True,
            route_reason="Test routing to sales"
        )
        yield mock


@pytest.fixture
def mock_sales_agent_respond():
    """Mock the SalesAgent.respond method at the instance level via the factory."""
    with patch("backend.app.agents.sales.SalesAgent.respond", new_callable=AsyncMock) as mock:
        mock.return_value = AgentResponse(
            content="Sales response",
            confidence=0.9,
            agent_name="SalesAgent"
        )
        yield mock


@pytest.mark.asyncio
async def test_conversation_service_routing_and_execution(db: AsyncSession, sample_customer, mock_router_sales, mock_sales_agent_respond):
    workspace, customer = sample_customer
    conversation_id = uuid4()

    response = await ConversationService.handle_message(
        db=db,
        workspace_id=workspace.id,
        customer_id=customer.id,
        conversation_id=conversation_id,
        query="I want to buy"
    )

    # Assert RouterService was called
    mock_router_sales.assert_called_once()

    # Assert SalesAgent was resolved and executed
    mock_sales_agent_respond.assert_called_once()

    assert response.content == "Sales response"
    assert response.agent_name == "SalesAgent"


@pytest.mark.asyncio
async def test_conversation_service_unregistered_agent(db: AsyncSession, sample_customer):
    workspace, customer = sample_customer
    conversation_id = uuid4()

    with patch("backend.app.services.conversation_service.RouterService.route_message", new_callable=AsyncMock) as mock_r:
        mock_r.return_value = RouteMessageResponse(
            decision=RouterDecision.HANDOFF,
            primary_intent=AgentIntent.SUPPORT,
            routed_agent=AgentIntent.SUPPORT,
            confidence=0.9,
            handoff_required=True,
            route_reason="Test"
        )

        response = await ConversationService.handle_message(
            db=db,
            workspace_id=workspace.id,
            customer_id=customer.id,
            conversation_id=conversation_id,
            query="Help me"
        )

        # Should fallback to graceful error since Support is not registered
        assert response.handoff_recommended is True
        assert response.requires_human is True
        assert "not quite sure" in response.content
