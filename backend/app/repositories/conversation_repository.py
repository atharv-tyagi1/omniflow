from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, List, Dict, Any

from backend.app.models.conversation import Conversation
from backend.app.models.message import Message


class ConversationRepository:
    @staticmethod
    async def create(
        db: AsyncSession, *, workspace_id: UUID, customer_id: UUID, channel: str = "web"
    ) -> Conversation:
        db_obj = Conversation(
            workspace_id=workspace_id, customer_id=customer_id, channel=channel
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_id(
        db: AsyncSession, conversation_id: UUID, workspace_id: UUID
    ) -> Optional[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.workspace_id == workspace_id,
            )
            .options(selectinload(Conversation.messages))
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_workspace(
        db: AsyncSession, workspace_id: UUID
    ) -> List[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.workspace_id == workspace_id)
            .order_by(Conversation.started_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_by_customer(
        db: AsyncSession, customer_id: UUID, channel: str
    ) -> Optional[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.customer_id == customer_id,
                Conversation.channel == channel,
                Conversation.status == "active",
            )
            .order_by(Conversation.started_at.desc())
        )
        return result.scalars().first()

    @staticmethod
    async def add_message(
        db: AsyncSession,
        *,
        conversation_id: UUID,
        sender_type: str,
        content: str,
        message_type: str = "text",
    ) -> Message:
        db_obj = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            content=content,
            message_type=message_type,
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def update(
        db: AsyncSession, *, db_obj: Conversation, obj_in: Dict[str, Any]
    ) -> Conversation:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_messages_by_conversation(
        db: AsyncSession, conversation_id: UUID
    ) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())
