from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.schemas.customer import CustomerCreate, CustomerUpdate
from backend.app.controllers.customer_controller import CustomerController
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.models.user import User

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("")
async def create_customer(
    data: CustomerCreate,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CustomerController.create_customer(db, workspace_id, data)


@router.get("")
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CustomerController.list_customers(db, workspace_id, skip, limit)


@router.get("/{customer_id}")
async def get_customer(
    customer_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CustomerController.get_customer(db, customer_id, workspace_id)


@router.put("/{customer_id}")
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CustomerController.update_customer(db, customer_id, workspace_id, data)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CustomerController.delete_customer(db, customer_id, workspace_id)
