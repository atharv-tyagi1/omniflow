from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.services.ticket_service import TicketService
from backend.app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
)
from backend.app.core.response import success_response
from uuid import UUID


class TicketController:
    @staticmethod
    async def create_ticket(
        db: AsyncSession, workspace_id: UUID, data: TicketCreate
    ) -> dict:
        ticket = await TicketService.create_ticket(db, workspace_id, data)
        resp = TicketResponse.model_validate(ticket)
        return success_response(resp.model_dump())

    @staticmethod
    async def get_ticket(db: AsyncSession, ticket_id: UUID, workspace_id: UUID) -> dict:
        ticket = await TicketService.get_ticket(db, ticket_id, workspace_id)
        resp = TicketResponse.model_validate(ticket)
        return success_response(resp.model_dump())

    @staticmethod
    async def list_tickets(
        db: AsyncSession, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> dict:
        tickets = await TicketService.list_tickets(db, workspace_id, skip, limit)
        return success_response(
            [TicketResponse.model_validate(t).model_dump() for t in tickets]
        )

    @staticmethod
    async def update_ticket(
        db: AsyncSession, ticket_id: UUID, workspace_id: UUID, data: TicketUpdate
    ) -> dict:
        ticket = await TicketService.update_ticket(db, ticket_id, workspace_id, data)
        resp = TicketResponse.model_validate(ticket)
        return success_response(resp.model_dump())
