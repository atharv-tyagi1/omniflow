from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
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
    async def upsert_by_external_id(
        db: AsyncSession, 
        workspace_id: UUID, 
        external_id: str, 
        name: str, 
        email: Optional[str] = None, 
        phone: Optional[str] = None
    ) -> Customer:
        """
        Safely and atomically upserts a Customer record matching (workspace_id, external_id).
        Does not overwrite trusted data if already exists, just ensures the record is present.
        """
        stmt = insert(Customer).values(
            workspace_id=workspace_id,
            external_id=external_id,
            name=name,
            email=email,
            phone=phone,
            status="active"
        )
        
        # Explicit field precedence: on conflict, we can either do nothing or update.
        # Let's say we update name if provided, but prefer existing. Actually, DO NOTHING 
        # is safest if we just want to ensure it exists, but we want to return the record.
        # DO UPDATE returning * allows us to get the full object back.
        stmt = stmt.on_conflict_do_update(
            index_elements=['workspace_id', 'external_id'],
            set_={
                "name": stmt.excluded.name,  # Or keep existing: Customer.name
                # We do not overwrite status if they are e.g. inactive
            }
        ).returning(Customer)

        result = await db.execute(stmt)
        await db.flush()
        return result.scalar_one()

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

    @staticmethod
    async def get_or_create_by_telegram_id(
        db: AsyncSession, telegram_id: str, name: str, workspace_id: UUID
    ) -> Customer:
        """
        Safely and atomically upserts a Customer record matching (workspace_id, telegram_id).
        Does not overwrite trusted data if already exists, just ensures the record is present.
        """
        stmt = insert(Customer).values(
            workspace_id=workspace_id,
            telegram_id=telegram_id,
            name=name,
            status="active"
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['workspace_id', 'telegram_id'],
            set_={
                "name": stmt.excluded.name,
            }
        ).returning(Customer)

        result = await db.execute(stmt)
        await db.flush()
        return result.scalar_one()
