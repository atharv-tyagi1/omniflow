import uuid
from typing import Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.public_auth import require_scope
from backend.app.core.rate_limiter import rate_limit
from backend.app.core.public_errors import PublicAPIException
from backend.app.schemas.public_api import PublicResponse, PublicCustomerSchema
from backend.app.models.customer import Customer

router = APIRouter(prefix="/customers", tags=["public_customers"])

@router.get("", response_model=PublicResponse[list[PublicCustomerSchema]])
async def list_customers(
    req: Request,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("chat")),
    _=Depends(rate_limit(limit=30, window_seconds=60))
):
    workspace_id = uuid.UUID(req.state.workspace_id)
    stmt = select(Customer).where(
        Customer.workspace_id == workspace_id
    ).order_by(Customer.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    customers = result.scalars().all()
    
    data = [
        PublicCustomerSchema(
            id=str(c.id),
            external_id=c.external_id,
            name=c.name,
            email=c.email,
            phone=c.phone,
            status=c.status
        ) for c in customers
    ]
    
    return PublicResponse(success=True, data=data, metadata={"limit": limit, "offset": offset, "count": len(data)})

@router.get("/{customer_id}", response_model=PublicResponse[PublicCustomerSchema])
async def get_customer(
    req: Request,
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("chat")),
    _=Depends(rate_limit(limit=60, window_seconds=60))
):
    workspace_id = uuid.UUID(req.state.workspace_id)
    stmt = select(Customer).where(
        Customer.workspace_id == workspace_id,
        Customer.id == customer_id
    )
    result = await db.execute(stmt)
    c = result.scalar_one_or_none()
    
    if not c:
        raise PublicAPIException("Customer not found", status_code=404, code="NOT_FOUND")
        
    data = PublicCustomerSchema(
        id=str(c.id),
        external_id=c.external_id,
        name=c.name,
        email=c.email,
        phone=c.phone,
        status=c.status
    )
    return PublicResponse(success=True, data=data)
