from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from backend.app.core.database import get_db
from backend.app.core.response import SuccessResponse, ErrorResponse
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.controllers.document_controller import DocumentController
from backend.app.schemas.domain import DocumentUpload, SearchQuery
from backend.app.models.user import User

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

@router.post("/documents", response_model=SuccessResponse)
async def upload_document(
    data: DocumentUpload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id)
):
    try:
        doc = await DocumentController.upload(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user.id,
            name=data.name,
            file_type=data.file_type,
            file_url=data.file_url,
            background_tasks=background_tasks
        )
        return SuccessResponse(data={"document_id": doc.id}, message="Document uploaded and processing started")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/documents", response_model=SuccessResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id)
):
    docs = await DocumentController.get_all(db=db, workspace_id=workspace_id)
    return SuccessResponse(data={"documents": [d.id for d in docs]}, message="Documents retrieved")

@router.post("/search", response_model=SuccessResponse)
async def search_knowledge(
    data: SearchQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id)
):
    try:
        chunks = await DocumentController.search(
            db=db,
            workspace_id=workspace_id,
            query=data.query,
            limit=data.limit
        )
        return SuccessResponse(data={"results_count": len(chunks)}, message="Search completed")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
