from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional

from backend.app.models.customer_care_case import CustomerCareCase

class CustomerCareCaseRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
        current_stage: str
    ) -> CustomerCareCase:
        db_obj = CustomerCareCase(
            workspace_id=workspace_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            current_stage=current_stage,
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_id(
        db: AsyncSession, case_id: UUID, workspace_id: UUID
    ) -> Optional[CustomerCareCase]:
        result = await db.execute(
            select(CustomerCareCase).where(
                CustomerCareCase.id == case_id, CustomerCareCase.workspace_id == workspace_id
            )
        )
        return result.scalars().first()

    @staticmethod
    async def update(db: AsyncSession, *, db_obj: CustomerCareCase, obj_in: dict) -> CustomerCareCase:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.flush()
        return db_obj

customer_care_case_repo = CustomerCareCaseRepository()
