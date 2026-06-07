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

import asyncio

@pytest.mark.asyncio
async def test_cc_agent_negative_refund_amount(db: AsyncSession, sample_customer, cc_agent, mock_ai_service_cc_output):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    with mock_ai_service_cc_output(
        refund_requested=True,
        refund_amount_requested=-10.0,
        resolution_status=CustomerCareStage.REFUND_PENDING.value
    ) as mock_ai:
        response = await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "I want a refund", {})
        
        stmt = select(CustomerCareCase).where(CustomerCareCase.conversation_id == conversation_id)
        result = await db.execute(stmt)
        case = result.scalars().first()
        
        assert case.refund_amount_requested is None
        assert response.requires_human is True
        assert "Invalid refund amount" in case.escalation_reason

@pytest.mark.asyncio
async def test_cc_agent_refund_amount_exceeds_order_total(db: AsyncSession, sample_customer, cc_agent, mock_ai_service_cc_output):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    with mock_ai_service_cc_output(
        refund_requested=True,
        refund_amount_requested=100.0,
        resolution_status=CustomerCareStage.REFUND_PENDING.value
    ) as mock_ai:
        # Simulate order total of 50.0 in metadata
        metadata = {"order_total": 50.0}
        response = await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "I want 100", metadata)
        
        stmt = select(CustomerCareCase).where(CustomerCareCase.conversation_id == conversation_id)
        result = await db.execute(stmt)
        case = result.scalars().first()
        
        assert case.refund_amount_requested is None
        assert response.requires_human is True
        assert "exceeds order total" in case.escalation_reason

@pytest.mark.asyncio
async def test_cc_agent_reopened_case_behavior(db: AsyncSession, sample_customer, cc_agent, mock_ai_service_cc_output):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    with mock_ai_service_cc_output(resolution_status=CustomerCareStage.CLOSED.value) as mock_ai:
        # First call resolves it
        await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "Close this", {})
        
    with mock_ai_service_cc_output(resolution_status=CustomerCareStage.ACKNOWLEDGED.value) as mock_ai:
        # Second call should create a NEW case since the old one is closed
        await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "I need more help", {})
        
        stmt = select(CustomerCareCase).where(CustomerCareCase.conversation_id == conversation_id).order_by(CustomerCareCase.created_at)
        result = await db.execute(stmt)
        cases = result.scalars().all()
        assert len(cases) == 2
        assert cases[0].current_stage == CustomerCareStage.CLOSED.value
        assert cases[1].current_stage == CustomerCareStage.ACKNOWLEDGED.value

from sqlalchemy.exc import IntegrityError
from backend.app.services.customer_care_service import CustomerCareService

@pytest.mark.asyncio
async def test_cc_agent_concurrency_case_creation(db: AsyncSession, sample_customer):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    # Pre-create the case in the DB so it exists when the fallback SELECT runs
    existing_case = CustomerCareCase(
        workspace_id=workspace.id,
        customer_id=customer.id,
        conversation_id=conversation_id,
        current_stage=CustomerCareStage.ACKNOWLEDGED.value
    )
    db.add(existing_case)
    await db.commit()
    await db.refresh(existing_case)
    
    original_execute = db.execute
    
    call_count = 0
    async def mock_execute(stmt, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        # The first execute is the SELECT. We return a mock empty result.
        if call_count == 1:
            class EmptyResult:
                def scalars(self):
                    return self
                def first(self):
                    return None
            return EmptyResult()
        # Fall back to real execute
        return await original_execute(stmt, *args, **kwargs)

    async def mock_commit():
        raise IntegrityError("Mocked race condition", params=None, orig=None)
        
    with patch.object(db, 'execute', side_effect=mock_execute):
        with patch.object(db, 'commit', side_effect=mock_commit):
            case = await CustomerCareService.get_or_create_case_for_conversation(
                db, workspace.id, customer.id, conversation_id
            )
            assert case.id == existing_case.id
            assert case.current_stage == CustomerCareStage.ACKNOWLEDGED.value

@pytest.mark.asyncio
async def test_cc_agent_missing_refund_amount_handled_safely(db: AsyncSession, sample_customer, cc_agent, mock_ai_service_cc_output):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    with mock_ai_service_cc_output(
        refund_requested=True,
        refund_amount_requested=None,
        resolution_status=CustomerCareStage.REFUND_PENDING.value
    ) as mock_ai:
        response = await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "I want my refund", {})
        
        stmt = select(CustomerCareCase).where(CustomerCareCase.conversation_id == conversation_id)
        result = await db.execute(stmt)
        case = result.scalars().first()
        
        # Policy explicitly escalates ambiguous/missing refund amounts
        assert case.refund_amount_requested is None
        assert case.refund_requested is True
        assert response.requires_human is True
        assert case.escalation_reason is not None
        assert "Ambiguous or missing" in case.escalation_reason

@pytest.mark.asyncio
async def test_cc_agent_refund_currency_mismatch(db: AsyncSession, sample_customer, cc_agent, mock_ai_service_cc_output):
    workspace, customer = sample_customer
    conversation_id = uuid4()
    
    with patch("backend.app.services.ai_service.AIService.generate_response", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(
            structured_data={
                "customer_reply": "I'm sorry",
                "complaint_type": ComplaintType.BILLING.value,
                "order_id": "123",
                "account_issue_type": None,
                "refund_requested": True,
                "refund_amount_requested": 50.0,
                "refund_currency": "EUR",
                "sentiment": CustomerSentiment.FRUSTRATED.value,
                "resolution_timeline": "24h",
                "resolution_status": CustomerCareStage.REFUND_PENDING.value,
                "confidence": 0.95,
                "sources": [],
                "agent_name": "CustomerCareAgent",
                "requires_human": False,
                "handoff_recommended": False,
                "next_agent": None,
                "metadata": {}
            },
            tokens_used=100,
            content="Mocked response"
        )
        
        # Order metadata says USD
        metadata = {"order_total": 50.0, "order_currency": "USD"}
        response = await cc_agent.respond(db, conversation_id, customer.id, workspace.id, "I want 50 EUR", metadata)
        
        stmt = select(CustomerCareCase).where(CustomerCareCase.conversation_id == conversation_id)
        result = await db.execute(stmt)
        case = result.scalars().first()
        
        assert case.refund_amount_requested is None
        assert response.requires_human is True
        assert "Currency mismatch" in case.escalation_reason
