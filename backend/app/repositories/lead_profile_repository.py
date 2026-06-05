from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from backend.app.models.lead_profile import LeadProfile
from backend.app.schemas.sales import SalesFunnelStage, BuyingIntent


class LeadProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_workspace_and_customer(
        self, workspace_id: UUID, customer_id: UUID
    ) -> Optional[LeadProfile]:
        """Fetches a specific lead profile."""
        query = select(LeadProfile).where(
            LeadProfile.workspace_id == workspace_id,
            LeadProfile.customer_id == customer_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def upsert(
        self,
        workspace_id: UUID,
        customer_id: UUID,
        **kwargs
    ) -> LeadProfile:
        """
        Inserts a new lead profile or updates an existing one for the given customer.
        Returns the created/updated profile.
        """
        # PostgreSQL specific upsert logic
        stmt = insert(LeadProfile).values(
            workspace_id=workspace_id,
            customer_id=customer_id,
            **kwargs
        )

        update_dict = {
            k: v for k, v in stmt.excluded.items() 
            if k not in ["id", "workspace_id", "customer_id", "created_at"] and k in kwargs
        }
        update_dict["updated_at"] = datetime.now(timezone.utc)

        stmt = stmt.on_conflict_do_update(
            index_elements=["workspace_id", "customer_id"],
            set_=update_dict
        ).returning(LeadProfile)

        result = await self.db.execute(stmt)
        # We don't commit here to allow service layer to orchestrate transactions
        return result.scalars().first()

    async def update_stage(
        self, workspace_id: UUID, customer_id: UUID, new_stage: SalesFunnelStage
    ) -> Optional[LeadProfile]:
        """Updates the funnel stage and records the timestamp."""
        stmt = (
            update(LeadProfile)
            .where(
                LeadProfile.workspace_id == workspace_id,
                LeadProfile.customer_id == customer_id,
            )
            .values(
                current_stage=new_stage,
                last_stage_change_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            .returning(LeadProfile)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def log_objection(
        self, workspace_id: UUID, customer_id: UUID, objection: str
    ) -> Optional[LeadProfile]:
        """Appends an objection to the JSONB list."""
        lead = await self.get_by_workspace_and_customer(workspace_id, customer_id)
        if not lead:
            return None
        
        objections = lead.objections or []
        if objection not in objections:
            objections.append(objection)
            
            stmt = (
                update(LeadProfile)
                .where(LeadProfile.id == lead.id)
                .values(objections=objections, updated_at=datetime.now(timezone.utc))
                .returning(LeadProfile)
            )
            result = await self.db.execute(stmt)
            return result.scalars().first()
        return lead

    async def update_buying_intent(
        self, workspace_id: UUID, customer_id: UUID, intent: BuyingIntent
    ) -> Optional[LeadProfile]:
        """Updates the buying intent."""
        stmt = (
            update(LeadProfile)
            .where(
                LeadProfile.workspace_id == workspace_id,
                LeadProfile.customer_id == customer_id,
            )
            .values(buying_intent=intent, updated_at=datetime.now(timezone.utc))
            .returning(LeadProfile)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_interaction(
        self, workspace_id: UUID, customer_id: UUID
    ) -> Optional[LeadProfile]:
        """Bumps the last_interaction_at timestamp."""
        stmt = (
            update(LeadProfile)
            .where(
                LeadProfile.workspace_id == workspace_id,
                LeadProfile.customer_id == customer_id,
            )
            .values(last_interaction_at=datetime.now(timezone.utc))
            .returning(LeadProfile)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
