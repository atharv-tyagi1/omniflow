import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.app.schemas.sales import SalesFunnelStage, BuyingIntent, LeadQualification
from backend.app.models.lead_profile import LeadProfile
from backend.app.models.customer import Customer
from backend.app.services.lead_profile_service import LeadProfileService
from backend.app.repositories.lead_profile_repository import LeadProfileRepository


from backend.app.models.workspace import Workspace
from backend.tests.conftest import TestingSessionLocal, engine
from backend.app.models.base import Base
import backend.app.models  # ensure models are loaded




@pytest.mark.asyncio
async def test_lead_profile_upsert(db: AsyncSession, sample_customer):
    workspace, customer = sample_customer
    
    # 1. Create via upsert
    qual = LeadQualification(budget="$10k", urgency="Q1", company_size="SMB")
    lead = await LeadProfileService.process_qualification(db, workspace.id, customer.id, qual)
    
    assert lead.budget == "$10k"
    assert lead.urgency == "Q1"
    assert lead.current_stage == SalesFunnelStage.new
    assert lead.last_interaction_at is not None

    # 2. Update via upsert
    qual2 = LeadQualification(use_case="CRM migration")
    lead_updated = await LeadProfileService.process_qualification(db, workspace.id, customer.id, qual2)
    
    # Assert id hasn't changed, but fields merged
    assert lead_updated.id == lead.id
    assert lead_updated.budget == "$10k"  # Retained
    assert lead_updated.use_case == "CRM migration"


@pytest.mark.asyncio
async def test_lead_stage_transitions(db: AsyncSession, sample_customer):
    workspace, customer = sample_customer
    qual = LeadQualification(budget="$10k")
    lead = await LeadProfileService.process_qualification(db, workspace.id, customer.id, qual)
    
    # Transition
    updated_lead = await LeadProfileService.move_to_stage(
        db, workspace.id, customer.id, SalesFunnelStage.discovery
    )
    assert updated_lead.current_stage == SalesFunnelStage.discovery
    
    updated_lead = await LeadProfileService.move_to_stage(
        db, workspace.id, customer.id, SalesFunnelStage.qualified
    )
    
    assert updated_lead is not None
    assert updated_lead.current_stage == SalesFunnelStage.qualified
    assert updated_lead.last_stage_change_at is not None
    
    # Invalid transition
    with pytest.raises(ValueError):
        await LeadProfileService.move_to_stage(
            db, workspace.id, customer.id, SalesFunnelStage.new
        )


@pytest.mark.asyncio
async def test_lead_duplicate_prevention(db: AsyncSession, sample_customer):
    workspace, customer = sample_customer
    
    # Manual insert of duplicate workspace+customer should fail UniqueConstraint
    lead1 = LeadProfile(workspace_id=workspace.id, customer_id=customer.id)
    lead2 = LeadProfile(workspace_id=workspace.id, customer_id=customer.id)
    
    db.add(lead1)
    await db.commit()
    
    db.add(lead2)
    with pytest.raises(IntegrityError):
        await db.commit()
    
    await db.rollback()


@pytest.mark.asyncio
async def test_lead_objection_logging(db: AsyncSession, sample_customer):
    workspace, customer = sample_customer
    qual = LeadQualification(budget="$10k")
    await LeadProfileService.process_qualification(db, workspace.id, customer.id, qual)
    
    lead = await LeadProfileService.log_objection(db, workspace.id, customer.id, "Too expensive")
    assert "Too expensive" in lead.objections
    
    # Prevent duplicate objections
    lead = await LeadProfileService.log_objection(db, workspace.id, customer.id, "Too expensive")
    assert lead.objections.count("Too expensive") == 1
    
    # Add new objection
    lead = await LeadProfileService.log_objection(db, workspace.id, customer.id, "Lacks feature X")
    assert "Lacks feature X" in lead.objections
    assert len(lead.objections) == 2


@pytest.mark.asyncio
async def test_lead_buying_intent_updates(db: AsyncSession, sample_customer):
    workspace, customer = sample_customer
    qual = LeadQualification(budget="$10k")
    await LeadProfileService.process_qualification(db, workspace.id, customer.id, qual)
    
    lead = await LeadProfileService.update_buying_intent(
        db, workspace.id, customer.id, BuyingIntent.high
    )
    assert lead.buying_intent == BuyingIntent.high


@pytest.mark.asyncio
async def test_lead_workspace_isolation(db: AsyncSession, sample_customer):
    workspace1, customer1 = sample_customer
    workspace2 = Workspace(id=uuid4(), name="Test Workspace 2", plan="free")
    db.add(workspace2)
    await db.commit()
    await db.refresh(workspace2)
    
    customer2 = Customer(id=uuid4(), workspace_id=workspace2.id, name="C2")
    db.add(customer2)
    await db.commit()
    
    qual = LeadQualification(budget="$10k")
    await LeadProfileService.process_qualification(db, workspace1.id, customer1.id, qual)
    await LeadProfileService.process_qualification(db, workspace2.id, customer2.id, qual)
    
    # Fetch from repo
    repo = LeadProfileRepository(db)
    lead_w2 = await repo.get_by_workspace_and_customer(workspace2.id, customer2.id)
    
    assert lead_w2 is not None
    assert lead_w2.workspace_id == workspace2.id
    
    # Attempting to fetch w1's customer in w2 should return None
    cross_tenant_lead = await repo.get_by_workspace_and_customer(workspace2.id, customer1.id)
    assert cross_tenant_lead is None


def test_lead_escalation_triggers_logic():
    # Tests the escalation conditions from the behavioral spec purely as a logic check
    # Escalate if: custom pricing, enterprise, legal, unsupported
    
    def check_escalation(query: str) -> bool:
        triggers = ["custom pricing", "discount", "enterprise", "sla", "legal", "gdpr", "soc2"]
        return any(t in query.lower() for t in triggers)
        
    assert check_escalation("I need custom pricing for 500 seats") is True
    assert check_escalation("Do you have SOC2 compliance?") is True
    assert check_escalation("What is your standard pricing?") is False
