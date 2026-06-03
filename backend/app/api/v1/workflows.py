from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from backend.app.core.database import get_db
from backend.app.core.response import SuccessResponse, ErrorResponse
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.controllers.workflow_controller import WorkflowController
from backend.app.schemas.domain import WorkflowCreate
from backend.app.models.user import User

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("/", response_model=SuccessResponse)
async def create_workflow(
    data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id)
):
    try:
        workflow = await WorkflowController.create(
            db=db,
            workspace_id=workspace_id,
            name=data.name,
            trigger_type=data.trigger_type
        )
        return SuccessResponse(data={"workflow_id": workflow.id}, message="Workflow created successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=SuccessResponse)
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id)
):
    workflows = await WorkflowController.get_all(db=db, workspace_id=workspace_id)
    return SuccessResponse(data={"workflows": [w.id for w in workflows]}, message="Workflows retrieved")

@router.post("/{workflow_id}/trigger", response_model=SuccessResponse)
async def trigger_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id)
):
    try:
        run = await WorkflowController.trigger(
            db=db,
            workspace_id=workspace_id,
            workflow_id=workflow_id
        )
        return SuccessResponse(
            data={"run_id": run.id, "status": run.status}, 
            message="Workflow triggered successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
