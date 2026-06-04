from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.ticket_repository import TicketRepository
from backend.app.schemas.ticket import TicketCreate, TicketUpdate
from backend.app.core.exceptions import NotFoundError
from uuid import UUID


class TicketService:
    @staticmethod
    async def create_ticket(db: AsyncSession, workspace_id: UUID, data: TicketCreate):
        return await TicketRepository.create(
            db,
            workspace_id=workspace_id,
            customer_id=data.customer_id,
            conversation_id=data.conversation_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
        )

    @staticmethod
    async def get_ticket(db: AsyncSession, ticket_id: UUID, workspace_id: UUID):
        ticket = await TicketRepository.get_by_id(db, ticket_id, workspace_id)
        if not ticket:
            raise NotFoundError("Ticket not found")
        return ticket

    @staticmethod
    async def list_tickets(
        db: AsyncSession, workspace_id: UUID, skip: int = 0, limit: int = 100
    ):
        return await TicketRepository.list_by_workspace(db, workspace_id, skip, limit)

    @staticmethod
    async def update_ticket(
        db: AsyncSession, ticket_id: UUID, workspace_id: UUID, data: TicketUpdate
    ):
        ticket = await TicketRepository.get_by_id(db, ticket_id, workspace_id)
        if not ticket:
            raise NotFoundError("Ticket not found")

        update_data = data.model_dump(exclude_unset=True)
        return await TicketRepository.update(db, db_obj=ticket, obj_in=update_data)
