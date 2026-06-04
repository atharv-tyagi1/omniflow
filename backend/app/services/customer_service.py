from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.schemas.customer import CustomerCreate, CustomerUpdate
from backend.app.core.exceptions import NotFoundError
from uuid import UUID


class CustomerService:
    @staticmethod
    async def create_customer(
        db: AsyncSession, workspace_id: UUID, data: CustomerCreate
    ):
        return await CustomerRepository.create(
            db,
            workspace_id=workspace_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
        )

    @staticmethod
    async def get_customer(db: AsyncSession, customer_id: UUID, workspace_id: UUID):
        customer = await CustomerRepository.get_by_id(db, customer_id, workspace_id)
        if not customer:
            raise NotFoundError("Customer not found")
        return customer

    @staticmethod
    async def list_customers(
        db: AsyncSession, workspace_id: UUID, skip: int = 0, limit: int = 100
    ):
        return await CustomerRepository.list_by_workspace(db, workspace_id, skip, limit)

    @staticmethod
    async def update_customer(
        db: AsyncSession, customer_id: UUID, workspace_id: UUID, data: CustomerUpdate
    ):
        customer = await CustomerRepository.get_by_id(db, customer_id, workspace_id)
        if not customer:
            raise NotFoundError("Customer not found")

        update_data = data.model_dump(exclude_unset=True)
        return await CustomerRepository.update(db, db_obj=customer, obj_in=update_data)

    @staticmethod
    async def delete_customer(db: AsyncSession, customer_id: UUID, workspace_id: UUID):
        deleted = await CustomerRepository.delete(db, customer_id, workspace_id)
        if not deleted:
            raise NotFoundError("Customer not found")
        return True
