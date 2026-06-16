from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.conversation_service import ConversationService
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message


class ConversationController:
    @staticmethod
    async def create(
        db: AsyncSession, workspace_id: UUID, customer_id: UUID, channel: str
    ) -> Conversation:
        return await ConversationService.create_conversation(
            db=db, workspace_id=workspace_id, customer_id=customer_id, channel=channel
        )

    @staticmethod
    async def get_all(db: AsyncSession, workspace_id: UUID) -> List[Conversation]:
        return await ConversationService.list_conversations(db, workspace_id)

    @staticmethod
    async def get_by_id(
        db: AsyncSession, conversation_id: UUID, workspace_id: UUID
    ) -> Conversation:
        return await ConversationService.get_conversation(
            db, conversation_id, workspace_id
        )

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: UUID,
        workspace_id: UUID,
        sender_type: str,
        content: str,
    ) -> Message:
        result = await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            sender_type=sender_type,
            content=content,
        )
        return result.customer_message

    @staticmethod
    async def list_messages(
        db: AsyncSession, conversation_id: UUID, workspace_id: UUID
    ) -> List[Message]:
        return await ConversationService.list_messages(
            db, conversation_id, workspace_id
        )
