import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.lead_profile import LeadProfile
from backend.app.repositories.lead_profile_repository import LeadProfileRepository
from backend.app.schemas.sales import SalesFunnelStage, BuyingIntent, LeadQualification

logger = logging.getLogger(__name__)

class LeadProfileService:
    @staticmethod
    async def get_lead(
        db: AsyncSession, workspace_id: UUID, customer_id: UUID
    ) -> Optional[LeadProfile]:
        """Fetch a specific lead profile."""
        repo = LeadProfileRepository(db)
        return await repo.get_by_workspace_and_customer(workspace_id, customer_id)

    @staticmethod
    async def process_qualification(
        db: AsyncSession,
        workspace_id: UUID,
        customer_id: UUID,
        qualification_data: LeadQualification,
    ) -> LeadProfile:
        """
        Upserts the lead profile with newly gathered qualification data.
        Determines stage transition logic if applicable.
        """
        repo = LeadProfileRepository(db)
        
        # Prepare kwargs from non-null qualification data
        kwargs = qualification_data.model_dump(exclude_unset=True, exclude_none=True)
        
        # Always bump interaction time
        lead = await repo.upsert(workspace_id, customer_id, **kwargs)
        await repo.update_interaction(workspace_id, customer_id)
        
        await db.commit()
        await db.refresh(lead)
        return lead

    @staticmethod
    async def move_to_stage(
        db: AsyncSession,
        workspace_id: UUID,
        customer_id: UUID,
        new_stage: SalesFunnelStage
    ) -> Optional[LeadProfile]:
        """Explicitly transitions a lead to a new funnel stage."""
        repo = LeadProfileRepository(db)
        lead = await repo.update_stage(workspace_id, customer_id, new_stage)
        if lead:
            await db.commit()
            await db.refresh(lead)
        return lead

    @staticmethod
    async def log_objection(
        db: AsyncSession, workspace_id: UUID, customer_id: UUID, objection: str
    ) -> Optional[LeadProfile]:
        """Logs a customer objection securely via repository."""
        repo = LeadProfileRepository(db)
        lead = await repo.log_objection(workspace_id, customer_id, objection)
        if lead:
            await db.commit()
            await db.refresh(lead)
        return lead

    @staticmethod
    async def update_buying_intent(
        db: AsyncSession, workspace_id: UUID, customer_id: UUID, intent: BuyingIntent
    ) -> Optional[LeadProfile]:
        """Updates the inferred buying intent."""
        repo = LeadProfileRepository(db)
        lead = await repo.update_buying_intent(workspace_id, customer_id, intent)
        if lead:
            await db.commit()
            await db.refresh(lead)
        return lead
