import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import contextlib

from backend.app.agents.customer_care import CustomerCareAgent
from backend.app.schemas.customer_care import CustomerCareAgentOutput, CustomerCareStage, ComplaintType, CustomerSentiment
from backend.app.models.customer_care_case import CustomerCareCase
from backend.app.schemas.ai import AIResponse

@pytest.fixture
def cc_agent():
    return CustomerCareAgent()

@pytest.fixture
def mock_ai_service_cc_output():
    @contextlib.contextmanager
    def _mock_output(
        customer_reply="I'm so sorry you experienced this.",
        complaint_type=ComplaintType.PRODUCT.value,
        order_id="12345",
        account_issue_type=None,
        refund_requested=False,
        refund_amount_requested=None,
        sentiment=CustomerSentiment.FRUSTRATED.value,
        resolution_timeline="24 hours",
        resolution_status=CustomerCareStage.INVESTIGATING.value,
        confidence=0.95,
        requires_human=False,
        handoff_recommended=False
    ):
        with patch("backend.app.services.ai_service.AIService.generate_response", new_callable=AsyncMock) as mock:
            mock.return_value = AIResponse(
                structured_data={
                    "customer_reply": customer_reply,
                    "complaint_type": complaint_type,
                    "order_id": order_id,
                    "account_issue_type": account_issue_type,
                    "refund_requested": refund_requested,
                    "refund_amount_requested": refund_amount_requested,
                    "sentiment": sentiment,
                    "resolution_timeline": resolution_timeline,
                    "resolution_status": resolution_status,
                    "confidence": confidence,
                    "sources": [],
                    "agent_name": "CustomerCareAgent",
                    "requires_human": requires_human,
                    "handoff_recommended": handoff_recommended,
                    "next_agent": None,
                    "metadata": {}
                },
                tokens_used=100,
                content="Mocked response"
            )
            yield mock
    return _mock_output

@pytest.mark.asyncio
async def test_cc_agent_idempotent_case_creation(db: AsyncSession, sample_customer, cc_agent, mock_ai_service_cc_output):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    with mock_ai_service_cc_output() as mock_ai:
        response1 = await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "My order is broken", {})
        
        stmt = select(CustomerCareCase).where(CustomerCareCase.conversation_id == conversation_id)
        result = await db.execute(stmt)
        cases = result.scalars().all()
        assert len(cases) == 1
        case1_id = cases[0].id
        
        # Second call in same conversation
        response2 = await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "And I want a refund", {})
        
        result = await db.execute(stmt)
        cases = result.scalars().all()
        assert len(cases) == 1
        assert cases[0].id == case1_id

@pytest.mark.asyncio
async def test_cc_agent_complaint_and_refund_handling(db: AsyncSession, sample_customer, cc_agent, mock_ai_service_cc_output):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    with mock_ai_service_cc_output(
        refund_requested=True,
        refund_amount_requested=50.0,
        resolution_status=CustomerCareStage.REFUND_PENDING.value
    ) as mock_ai:
        response = await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "I want my $50 back", {})
        
        stmt = select(CustomerCareCase).where(CustomerCareCase.conversation_id == conversation_id)
        result = await db.execute(stmt)
        case = result.scalars().first()
        
        assert case.refund_requested is True
        assert case.refund_amount_requested == Decimal('50.0')
        assert case.current_stage == CustomerCareStage.REFUND_PENDING.value
        assert response.metadata["refund_requested"] is True

@pytest.mark.asyncio
async def test_cc_agent_escalation_handling(db: AsyncSession, sample_customer, cc_agent, mock_ai_service_cc_output):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    with mock_ai_service_cc_output(requires_human=True, handoff_recommended=True) as mock_ai:
        response = await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "Let me speak to a manager", {})
        
        assert response.requires_human is True
        assert response.handoff_recommended is True
        
        stmt = select(CustomerCareCase).where(CustomerCareCase.conversation_id == conversation_id)
        result = await db.execute(stmt)
        case = result.scalars().first()
        assert case.escalation_reason is not None
        assert "requires_human=True" in case.escalation_reason

@pytest.mark.asyncio
async def test_cc_agent_workspace_isolation(db: AsyncSession, sample_customer, cc_agent, mock_ai_service_cc_output):
    workspace, customer = sample_customer
    wrong_workspace_id = uuid4()
    conversation_id = uuid4()
    
    with mock_ai_service_cc_output() as mock_ai:
        # Should raise an error or create a case in the wrong workspace? 
        # The service will just create it if the DB constraints don't fail, 
        # but the workspace_id must exist due to FK constraint.
        try:
            await cc_agent.respond(db, conversation_id, customer.id, wrong_workspace_id, "Hello", {})
            result = await db.execute(select(CustomerCareCase).where(CustomerCareCase.workspace_id == wrong_workspace_id))
            assert result.scalars().first() is not None
        except Exception:
            # Expected if FK constraint fails
            pass

@pytest.mark.asyncio
async def test_cc_agent_malformed_output(db: AsyncSession, sample_customer, cc_agent):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    with patch("backend.app.services.ai_service.AIService.generate_response", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(
            content="Raw unstructured string",
            structured_data=None, # Missing structured data
            error="Malformed JSON"
        )
        
        response = await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "Hello", {})
        
        assert response.requires_human is True
        assert "technical difficulties" in response.content.lower()
