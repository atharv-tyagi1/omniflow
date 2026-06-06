import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.sales import SalesAgent
from backend.app.schemas.ai import AIResponse
from backend.app.schemas.sales import SalesAgentOutput, SalesFunnelStage, BuyingIntent, LeadQualification
from backend.app.schemas.agent import AgentResponse, AgentContext
from backend.app.services.lead_profile_service import LeadProfileService


@pytest.fixture
def sample_sales_output():
    return SalesAgentOutput(
        customer_reply="I can certainly help you with enterprise pricing.",
        lead_score=85,
        budget="$50k",
        urgency="Q3",
        company_size="Enterprise",
        use_case="CRM integration",
        buying_intent=BuyingIntent.high,
        current_stage=SalesFunnelStage.discovery,
        objections=["Too expensive"],
        requires_human=True,
        handoff_recommended=True,
        next_agent="human",
        next_best_action="Schedule demo"
    )


@pytest.fixture
def mock_context_builder():
    """Mock AgentContextBuilder to avoid DB lookups during context assembly."""
    with patch("backend.app.agents.sales.AgentContextBuilder.build_context") as mock:
        mock.return_value = AgentContext(
            conversation_history=[],
            rag_context=[],
            workspace_context={"id": "test-workspace"},
            customer_context={"id": "test-customer"},
            conversation_state={"status": "active"},
            router_metadata={},
        )
        yield mock


@pytest.fixture
def mock_ai_service(sample_sales_output):
    with patch("backend.app.agents.sales.AIService.generate_response") as mock:
        mock.return_value = AIResponse(
            content="Structured response",
            structured_data=sample_sales_output.model_dump(),
            tokens_used=150,
        )
        yield mock


@pytest.mark.asyncio
async def test_sales_agent_execution_and_escalation(db: AsyncSession, sample_customer, mock_ai_service, mock_context_builder):
    workspace, customer = sample_customer
    conversation_id = uuid4()

    agent = SalesAgent()

    response = await agent.respond(
        db=db,
        conversation_id=conversation_id,
        customer_id=customer.id,
        workspace_id=workspace.id,
        query="I need custom enterprise pricing.",
        router_metadata={"intent": "sales"}
    )

    assert isinstance(response, AgentResponse)
    assert response.requires_human is True
    assert response.handoff_recommended is True
    assert response.next_agent == "human"

    # Check that lead profile was created/updated
    lead = await LeadProfileService.get_lead(db, workspace.id, customer.id)
    assert lead is not None
    assert lead.budget == "$50k"
    assert lead.company_size == "Enterprise"
    assert lead.current_stage == SalesFunnelStage.discovery
    assert "Too expensive" in lead.objections


@pytest.mark.asyncio
async def test_sales_agent_malformed_output(db: AsyncSession, sample_customer, mock_context_builder):
    workspace, customer = sample_customer
    conversation_id = uuid4()

    agent = SalesAgent()

    with patch("backend.app.agents.sales.AIService.generate_response") as mock_ai:
        # Simulate malformed output (no structured data)
        mock_ai.return_value = AIResponse(
            content="Just a string",
            structured_data=None,
            error="Malformed JSON"
        )

        response = await agent.respond(
            db=db,
            conversation_id=conversation_id,
            customer_id=customer.id,
            workspace_id=workspace.id,
            query="Hello",
            router_metadata={}
        )

        # Should hit handle_error
        assert response.requires_human is True
        assert "technical difficulties" in response.content


@pytest.mark.asyncio
async def test_sales_agent_invalid_transition(db: AsyncSession, sample_customer, mock_ai_service, mock_context_builder):
    workspace, customer = sample_customer
    conversation_id = uuid4()

    # Force the lead into 'converted' stage first
    await LeadProfileService.process_qualification(
        db, workspace.id, customer.id,
        qualification_data=LeadQualification(
            budget="$100k"
        )
    )

    await LeadProfileService.move_to_stage(db, workspace.id, customer.id, SalesFunnelStage.discovery)
    await LeadProfileService.move_to_stage(db, workspace.id, customer.id, SalesFunnelStage.qualified)
    await LeadProfileService.move_to_stage(db, workspace.id, customer.id, SalesFunnelStage.ready_to_buy)
    await LeadProfileService.move_to_stage(db, workspace.id, customer.id, SalesFunnelStage.converted)

    # Now run agent, mock will try to set stage to 'discovery' (invalid from converted)
    agent = SalesAgent()
    response = await agent.respond(
        db=db,
        conversation_id=conversation_id,
        customer_id=customer.id,
        workspace_id=workspace.id,
        query="Wait go back.",
        router_metadata={}
    )

    # The agent should catch the ValueError from move_to_stage and continue smoothly
    assert response.requires_human is True  # Based on mock output

    # Verify stage was NOT changed back
    lead = await LeadProfileService.get_lead(db, workspace.id, customer.id)
    assert lead.current_stage == SalesFunnelStage.converted
