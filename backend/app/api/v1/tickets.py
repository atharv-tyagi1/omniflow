from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.schemas.ticket import TicketCreate, TicketUpdate
from backend.app.controllers.ticket_controller import TicketController
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.models.user import User

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("")
async def create_ticket(
    data: TicketCreate,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await TicketController.create_ticket(db, workspace_id, data)


@router.get("")
async def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await TicketController.list_tickets(db, workspace_id, skip, limit)


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: UUID,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await TicketController.get_ticket(db, ticket_id, workspace_id)


@router.put("/{ticket_id}")
async def update_ticket(
    ticket_id: UUID,
    data: TicketUpdate,
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await TicketController.update_ticket(db, ticket_id, workspace_id, data)
