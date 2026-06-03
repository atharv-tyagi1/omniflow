from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.models.ticket import Ticket
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.core.ai.gemini_client import GeminiClient

class OutreachService:
    @staticmethod
    async def evaluate_triggers(db: AsyncSession):
        """
        Periodically evaluate configured workflows across workspaces.
        For a hackathon MVP, we hardcode two core outreach rules based on the PRD:
        1. Open Ticket > 3 Days
        2. Inactive Lead > 48 Hours
        """
        now = datetime.now(timezone.utc)
        
        # 1. Stale Tickets Outreach
        # Find tickets open for > 3 days (for demo purposes, we will treat > 3 minutes as stale if needed)
        stale_threshold = now - timedelta(days=3)
        stmt = select(Ticket).where(
            and_(
                Ticket.status == "open",
                Ticket.created_at < stale_threshold
            )
        )
        result = await db.execute(stmt)
        stale_tickets = result.scalars().all()
        
        for ticket in stale_tickets:
            await OutreachService._trigger_ticket_outreach(db, ticket)
            
        # 2. Inactive Lead Outreach
        # Conversations untouched for 48 hours
        inactive_threshold = now - timedelta(hours=48)
        stmt2 = select(Conversation).where(
            and_(
                Conversation.status == "active",
                Conversation.started_at < inactive_threshold
                # In a real app we'd join messages to find the last message time
            )
        )
        result2 = await db.execute(stmt2)
        inactive_convos = result2.scalars().all()
        
        for convo in inactive_convos:
            await OutreachService._trigger_lead_outreach(db, convo)
            
    @staticmethod
    async def _trigger_ticket_outreach(db: AsyncSession, ticket: Ticket):
        """Generate and send an automated follow-up for a stale ticket."""
        prompt = f"""
        You are an AI Customer Care assistant.
        A customer has a support ticket titled '{ticket.title}'.
        The ticket has been open for several days without resolution.
        Draft a polite, empathetic follow-up message to the customer assuring them we are still looking into it.
        Keep it under 3 sentences.
        """
        client = GeminiClient.get_instance()
        try:
            # We use the generic chat generation here
            response_text = await client.generate_chat_response([{"role": "user", "content": prompt}], "You are a customer care agent.")
            
            # Save the proactive message to the conversation
            new_message = Message(
                conversation_id=ticket.conversation_id,
                content=response_text,
                sender_type="agent",
                sender_id="system_outreach",
                metadata={"is_proactive": True, "trigger": "stale_ticket"}
            )
            db.add(new_message)
            await db.commit()
            print(f"[Outreach] Triggered follow-up for Ticket {ticket.id}")
        except Exception as e:
            print(f"[Outreach] Failed to trigger ticket outreach: {e}")

    @staticmethod
    async def _trigger_lead_outreach(db: AsyncSession, convo: Conversation):
        """Generate and send an automated follow-up for an inactive conversation."""
        prompt = f"""
        You are an AI Sales assistant.
        A user started a conversation with us a few days ago but hasn't responded.
        Draft a friendly, low-pressure re-engagement message to see if they still need help or have questions.
        Keep it under 3 sentences.
        """
        client = GeminiClient.get_instance()
        try:
            response_text = await client.generate_chat_response([{"role": "user", "content": prompt}], "You are a sales agent.")
            
            new_message = Message(
                conversation_id=convo.id,
                content=response_text,
                sender_type="agent",
                sender_id="system_outreach",
                metadata={"is_proactive": True, "trigger": "inactive_lead"}
            )
            db.add(new_message)
            await db.commit()
            print(f"[Outreach] Triggered follow-up for Conversation {convo.id}")
        except Exception as e:
            print(f"[Outreach] Failed to trigger lead outreach: {e}")
