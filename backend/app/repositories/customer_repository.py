from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional

from backend.app.models.customer import Customer

class CustomerRepository:
    @staticmethod
    async def get_by_telegram_id(db: AsyncSession, telegram_id: str, workspace_id: UUID) -> Optional[Customer]:
        result = await db.execute(
            select(Customer)
            .where(Customer.telegram_id == telegram_id, Customer.workspace_id == workspace_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_or_create_by_telegram_id(
        db: AsyncSession, 
        telegram_id: str, 
        name: str, 
        workspace_id: UUID
    ) -> Customer:
        # Check if exists
        existing = await CustomerRepository.get_by_telegram_id(db, telegram_id, workspace_id)
        if existing:
            return existing
        
        # Create new
        new_customer = Customer(
            workspace_id=workspace_id,
            name=name,
            telegram_id=telegram_id,
        )
        db.add(new_customer)
        await db.flush()
        return new_customer
