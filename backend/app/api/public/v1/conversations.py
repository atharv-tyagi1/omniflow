import uuid
from typing import Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.public_auth import require_scope
from backend.app.core.rate_limiter import rate_limit
from backend.app.core.public_errors import PublicAPIException
from backend.app.schemas.public_api import PublicResponse, PublicConversationSchema
from backend.app.models.conversation import Conversation

router = APIRouter(prefix="/conversations", tags=["public_conversations"])

@router.get("", response_model=PublicResponse[list[PublicConversationSchema]])
async def list_conversations(
    req: Request,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("chat")),
    _=Depends(rate_limit(limit=30, window_seconds=60))
):
    workspace_id = uuid.UUID(req.state.workspace_id)
    stmt = select(Conversation).where(
        Conversation.workspace_id == workspace_id
    ).order_by(Conversation.started_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    conversations = result.scalars().all()
    
    data = [
        PublicConversationSchema(
            id=str(c.id),
            customer_id=str(c.customer_id),
            external_id=c.external_id,
            channel=c.channel,
            status=c.status,
            started_at=c.started_at.isoformat()
        ) for c in conversations
    ]
    
    return PublicResponse(success=True, data=data, metadata={"limit": limit, "offset": offset, "count": len(data)})

@router.get("/{conversation_id}", response_model=PublicResponse[PublicConversationSchema])
async def get_conversation(
    req: Request,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("chat")),
    _=Depends(rate_limit(limit=60, window_seconds=60))
):
    workspace_id = uuid.UUID(req.state.workspace_id)
    stmt = select(Conversation).where(
        Conversation.workspace_id == workspace_id,
        Conversation.id == conversation_id
    )
    result = await db.execute(stmt)
    c = result.scalar_one_or_none()
    
    if not c:
        raise PublicAPIException("Conversation not found", status_code=404, code="NOT_FOUND")
        
    data = PublicConversationSchema(
        id=str(c.id),
        customer_id=str(c.customer_id),
        external_id=c.external_id,
        channel=c.channel,
        status=c.status,
        started_at=c.started_at.isoformat()
    )
    return PublicResponse(success=True, data=data)
