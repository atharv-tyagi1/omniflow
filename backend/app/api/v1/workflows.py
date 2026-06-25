from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.core.response import SuccessResponse
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.controllers.workflow_controller import WorkflowController
from backend.app.schemas.domain import WorkflowCreate
from backend.app.schemas.workflow_builder import WorkflowDraftUpdate
from backend.app.models.user import User

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("/", response_model=SuccessResponse)
async def create_workflow(
    data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        workflow = await WorkflowController.create(
            db=db,
            workspace_id=workspace_id,
            name=data.name,
            trigger_type=data.trigger_type,
        )
        return SuccessResponse(
            data={"workflow_id": workflow.id}, message="Workflow created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=SuccessResponse)
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    workflows = await WorkflowController.get_all(db=db, workspace_id=workspace_id)
    serialized = [
        {
            "id": w.id,
            "name": w.name,
            "trigger_type": w.trigger_type,
            "status": w.status,
            "created_at": w.created_at
        } for w in workflows
    ]
    return SuccessResponse(
        data={"workflows": serialized}, message="Workflows retrieved"
    )


@router.post("/{workflow_id}/trigger", response_model=SuccessResponse)
async def trigger_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        run = await WorkflowController.trigger(
            db=db, workspace_id=workspace_id, workflow_id=workflow_id
        )
        return SuccessResponse(
            data={"run_id": run.id, "status": run.status},
            message="Workflow triggered successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{workflow_id}", response_model=SuccessResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        data = await WorkflowController.get_workflow_draft(db, workspace_id, workflow_id)
        return SuccessResponse(data=data, message="Workflow retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{workflow_id}/draft", response_model=SuccessResponse)
async def save_workflow_draft(
    workflow_id: UUID,
    draft: WorkflowDraftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        res = await WorkflowController.save_draft(db, workspace_id, workflow_id, draft)
        return SuccessResponse(data=res, message="Draft saved successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{workflow_id}/publish", response_model=SuccessResponse)
async def publish_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        res = await WorkflowController.publish(db, workspace_id, workflow_id)
        return SuccessResponse(data=res, message="Workflow published successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{workflow_id}/runs", response_model=SuccessResponse)
async def list_workflow_runs(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        runs = await WorkflowController.list_runs(db, workspace_id, workflow_id)
        serialized = [
            {
                "id": str(r.id),
                "status": r.status,
                "executed_at": r.executed_at,
                "execution_log": r.execution_log
            } for r in runs
        ]
        return SuccessResponse(data={"runs": serialized}, message="Runs retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{workflow_id}/runs/{run_id}", response_model=SuccessResponse)
async def get_workflow_run_details(
    workflow_id: UUID,
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        run = await WorkflowController.get_run_details(db, workspace_id, workflow_id, run_id)
        serialized = {
            "id": str(run.id),
            "status": run.status,
            "executed_at": run.executed_at,
            "execution_log": run.execution_log,
            "steps": [
                {
                    "id": str(s.id),
                    "node_id": str(s.node_id),
                    "status": s.status,
                    "input_payload": s.input_payload,
                    "output_payload": s.output_payload,
                    "error_payload": s.error_payload,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at
                } for s in run.steps
            ]
        }
        return SuccessResponse(data=serialized, message="Run details retrieved successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
