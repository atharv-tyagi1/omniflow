from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.customer_service import CustomerService
from backend.app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)
from backend.app.core.response import success_response
from uuid import UUID


class CustomerController:
    @staticmethod
    async def create_customer(
        db: AsyncSession, workspace_id: UUID, data: CustomerCreate
    ) -> dict:
        customer = await CustomerService.create_customer(db, workspace_id, data)
        resp = CustomerResponse.model_validate(customer)
        return success_response(resp.model_dump())

    @staticmethod
    async def get_customer(
        db: AsyncSession, customer_id: UUID, workspace_id: UUID
    ) -> dict:
        customer = await CustomerService.get_customer(db, customer_id, workspace_id)
        resp = CustomerResponse.model_validate(customer)
        return success_response(resp.model_dump())

    @staticmethod
    async def list_customers(
        db: AsyncSession, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> dict:
        customers = await CustomerService.list_customers(
            db, workspace_id, skip, limit
        )
        return success_response(
            [CustomerResponse.model_validate(c).model_dump() for c in customers]
        )

    @staticmethod
    async def update_customer(
        db: AsyncSession, customer_id: UUID, workspace_id: UUID, data: CustomerUpdate
    ) -> dict:
        customer = await CustomerService.update_customer(
            db, customer_id, workspace_id, data
        )
        resp = CustomerResponse.model_validate(customer)
        return success_response(resp.model_dump())

    @staticmethod
    async def delete_customer(
        db: AsyncSession, customer_id: UUID, workspace_id: UUID
    ) -> dict:
        await CustomerService.delete_customer(db, customer_id, workspace_id)
        return success_response({"deleted": True})
