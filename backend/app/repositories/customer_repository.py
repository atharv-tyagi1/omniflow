from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional

from backend.app.models.customer import Customer


class CustomerRepository:
    @staticmethod
    async def create(db: AsyncSession, *, workspace_id: UUID, name: str, email: Optional[str] = None, phone: Optional[str] = None) -> Customer:
        db_obj = Customer(workspace_id=workspace_id, name=name, email=email, phone=phone)
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_id(db: AsyncSession, customer_id: UUID, workspace_id: UUID) -> Optional[Customer]:
        result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.workspace_id == workspace_id))
        return result.scalars().first()

    @staticmethod
    async def list_by_workspace(db: AsyncSession, workspace_id: UUID, skip: int = 0, limit: int = 100) -> list[Customer]:
        result = await db.execute(select(Customer).where(Customer.workspace_id == workspace_id).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, *, db_obj: Customer, obj_in: dict) -> Customer:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def delete(db: AsyncSession, customer_id: UUID, workspace_id: UUID) -> bool:
        result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.workspace_id == workspace_id))
        customer = result.scalars().first()
        if customer:
            await db.delete(customer)
            await db.flush()
            return True
        return False
