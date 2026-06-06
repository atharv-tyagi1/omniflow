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

    @staticmethod
    async def get_or_create_ticket_for_conversation(
        db: AsyncSession,
        workspace_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
        title: str = "Support Session"
    ):
        """Idempotently load or create a ticket for a conversation."""
        from sqlalchemy.future import select
        from backend.app.models.ticket import Ticket
        
        # Check for open or in_progress ticket for this conversation
        stmt = select(Ticket).where(
            Ticket.workspace_id == workspace_id,
            Ticket.conversation_id == conversation_id,
            Ticket.status.in_(["open", "in_progress"])
        ).limit(1)
        
        result = await db.execute(stmt)
        ticket = result.scalars().first()
        
        if ticket:
            return ticket
            
        # Create a new ticket if none exists
        return await TicketRepository.create(
            db,
            workspace_id=workspace_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            title=title,
            description="Auto-generated support ticket.",
            priority="medium"
        )
        
    @staticmethod
    async def update_support_context(
        db: AsyncSession,
        workspace_id: UUID,
        ticket_id: UUID,
        issue_type: str,
        probable_cause: str,
        last_troubleshooting_step: str,
        status: str,
        escalation_reason: str = None
    ):
        from datetime import datetime, timezone
        ticket = await TicketRepository.get_by_id(db, ticket_id, workspace_id)
        if not ticket:
            raise NotFoundError("Ticket not found")
            
        update_data = {
            "issue_type": issue_type,
            "probable_cause": probable_cause,
            "last_troubleshooting_step": last_troubleshooting_step,
            "status": status,
            "last_interaction_at": datetime.now(timezone.utc)
        }
        if escalation_reason:
            update_data["escalation_reason"] = escalation_reason
            
        return await TicketRepository.update(db, db_obj=ticket, obj_in=update_data)
