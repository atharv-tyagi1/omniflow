from fastapi import APIRouter, Depends, HTTPException
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User as UserResponse
from backend.app.schemas.agent_builder import AgentTemplateResponse

router = APIRouter()

@router.get("", response_model=List[AgentTemplateResponse])
async def list_templates(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """List available agent templates."""
    # Stub: we don't have an AgentTemplate model yet, returning empty
    return []

@router.post("/{template_id}/instantiate")
async def instantiate_template(
    workspace_id: uuid.UUID,
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new agent from a template."""
    raise HTTPException(status_code=501, detail="Not implemented")
