from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.schemas.router import RouteMessageRequest, RouteMessageResponse
from backend.app.core.response import SuccessResponse
from backend.app.core.database import get_db
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.models.user import User
from backend.app.services.router_service import RouterService
from backend.app.controllers.conversation_controller import ConversationController
from backend.app.api.v1.api_keys import router as api_keys_router
from backend.app.api.v1.agents import router as agents_router


router = APIRouter(prefix="/router", tags=["router"])
# We should probably mount api_keys to a main v1 APIRouter, but this file is named `router.py`.
# Wait, let me check how other v1 routers are mounted in main.py.


@router.post("/route", response_model=SuccessResponse)
async def route_message(
    data: RouteMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """
    Evaluates a user message against the Smart Intent Router to determine agent routing policy.
    Does not generate a text response to the user.
    """
    try:
        # Fetch conversation to get state
        conversation = await ConversationController.get_by_id(
            db=db, conversation_id=data.conversation_id, workspace_id=workspace_id
        )
        
        # We fetch recent messages as history for context (optional, simple string format)
        messages = await ConversationController.get_messages(
            db=db, conversation_id=data.conversation_id, workspace_id=workspace_id
        )
        
        history = []
        for msg in messages[-6:]:
            sender = "User" if msg.sender_type == "customer" else "AI"
            history.append(f"{sender}: {msg.content}")

        route_response = await RouterService.route_message(
            db=db,
            request=data,
            conversation=conversation,
            history=history
        )
        
        return SuccessResponse(
            data=route_response.model_dump(),
            message="Message routed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Routing failed: {str(e)}"
        )
