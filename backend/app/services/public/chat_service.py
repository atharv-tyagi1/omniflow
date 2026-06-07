import uuid
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

class PublicChatService:
    @staticmethod
    async def process_sync_chat(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        external_customer_id: str,
        customer_name: str,
        message: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        conversation_external_id: Optional[str] = None
    ) -> dict:
        """
        Executes a single chat request idempotently. 
        Returns a dict suitable for PublicChatResponse.
        """
        # Atomic UPSERT for customer identity via Repository
        customer = await CustomerRepository.upsert_by_external_id(
            db=db,
            workspace_id=workspace_id,
            external_id=external_customer_id,
            name=customer_name,
            email=customer_email,
            phone=customer_phone
        )

        # Re-use conversation_service logic for idempotency on conversation
        conversation = await ConversationService.get_active_by_customer(db=db, customer_id=customer.id, channel="public_api")
        if not conversation:
            conversation = await ConversationService.create_conversation(
                db=db,
                workspace_id=workspace_id,
                customer_id=customer.id,
                channel="public_api"
            )
            if conversation_external_id:
                conversation.external_id = conversation_external_id
                await db.commit()

        # Route message
        await ConversationService.add_message(
            db=db,
            conversation_id=conversation.id,
            workspace_id=workspace_id,
            sender_type="customer",
            content=message
        )

        history = await ConversationService.list_messages(db=db, conversation_id=conversation.id, workspace_id=workspace_id)
        if history:
            latest = history[-1]
            return {
                "conversation_id": str(conversation.id),
                "message_id": str(latest.id),
                "content": latest.content,
                "agent_name": latest.sender_type if latest.sender_type != "customer" else "Agent"
            }
            
        raise Exception("No response generated")
