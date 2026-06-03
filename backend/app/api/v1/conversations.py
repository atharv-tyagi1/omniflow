import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.core.response import SuccessResponse
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.controllers.conversation_controller import ConversationController
from backend.app.schemas.domain import ConversationCreate, MessageCreate
from backend.app.models.user import User

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("/", response_model=SuccessResponse)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        conversation = await ConversationController.create(
            db=db,
            workspace_id=workspace_id,
            customer_id=data.customer_id,
            channel=data.channel,
        )
        return SuccessResponse(
            data={"conversation_id": conversation.id},
            message="Conversation created successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=SuccessResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    conversations = await ConversationController.get_all(
        db=db, workspace_id=workspace_id
    )
    return SuccessResponse(
        data={"conversations": [c.id for c in conversations]},
        message="Conversations retrieved",
    )


@router.post("/{conversation_id}/analyze")
async def analyze_conversation_intel(
    conversation_id: UUID, db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger the conversation intel analysis to extract sentiment and topics.
    """
    from backend.app.services.intel_service import IntelService

    try:
        result = await IntelService.analyze_conversation(db, conversation_id)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["reason"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Failed to analyze conversation {conversation_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=SuccessResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        conversation = await ConversationController.get_by_id(
            db=db, conversation_id=conversation_id, workspace_id=workspace_id
        )
        return SuccessResponse(
            data={
                "conversation": {
                    "id": conversation.id,
                    "customer_id": conversation.customer_id,
                    "channel": conversation.channel,
                    "status": conversation.status,
                }
            },
            message="Conversation retrieved successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{conversation_id}/messages", response_model=SuccessResponse)
async def list_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        messages = await ConversationController.list_messages(
            db=db, conversation_id=conversation_id, workspace_id=workspace_id
        )
        # Serialize messages
        msg_list = [
            {
                "id": m.id,
                "sender_type": m.sender_type,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
        return SuccessResponse(
            data={"messages": msg_list}, message="Messages retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{conversation_id}/messages", response_model=SuccessResponse)
async def add_message(
    conversation_id: UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        msg = await ConversationController.add_message(
            db=db,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            sender_type=data.sender_type,
            content=data.content,
        )
        return SuccessResponse(
            data={"message_id": msg.id}, message="Message added successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{conversation_id}/classify", response_model=SuccessResponse)
async def classify_message(
    conversation_id: UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Classify a message's intent without generating an agent response."""
    try:
        from backend.app.services.conversation_service import ConversationService

        intent = await ConversationService.classify_message(data.content)
        return SuccessResponse(
            data=intent.to_dict(), message="Intent classified successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
