from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.core.response import SuccessResponse
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.controllers.dataset_controller import DatasetController
from backend.app.schemas.domain import DatasetUpload, DatasetQueryRequest
from backend.app.models.user import User

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/", response_model=SuccessResponse)
async def upload_dataset(
    data: DatasetUpload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        dataset = await DatasetController.upload(
            db=db,
            workspace_id=workspace_id,
            name=data.name,
            file_url=data.file_url,
            row_count=data.row_count,
            column_count=data.column_count,
        )
        return SuccessResponse(
            data={"dataset_id": dataset.id}, message="Dataset registered successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=SuccessResponse)
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    datasets = await DatasetController.get_all(db=db, workspace_id=workspace_id)
    return SuccessResponse(
        data={"datasets": [d.id for d in datasets]}, message="Datasets retrieved"
    )


@router.post("/{dataset_id}/query", response_model=SuccessResponse)
async def ask_question(
    dataset_id: UUID,
    data: DatasetQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        query_result = await DatasetController.ask_question(
            db=db,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            question=data.question,
        )
        return SuccessResponse(
            data={
                "answer": query_result.answer,
                "chart_config": query_result.chart_config,
            },
            message="Query analyzed successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
