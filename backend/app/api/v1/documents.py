import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.core.response import SuccessResponse
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.controllers.document_controller import DocumentController
from backend.app.schemas.domain import DocumentUpload, SearchQuery
from backend.app.models.user import User

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads")


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=SuccessResponse)
async def upload_document_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """
    Accept a real file upload (multipart/form-data).
    Saves the file locally and triggers background RAG processing.
    """
    try:
        _ensure_upload_dir()
        safe_filename = os.path.basename(file.filename or "upload.bin").replace(" ", "_")
        save_path = os.path.join(UPLOAD_DIR, f"{workspace_id}_{safe_filename}")

        async with aiofiles.open(save_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        file_url = f"file://{save_path}"
        display_name = name or safe_filename
        mime_type = file.content_type or "application/octet-stream"

        doc = await DocumentController.upload(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user.id,
            name=display_name,
            file_type=mime_type,
            file_url=file_url,
            background_tasks=background_tasks,
        )
        return SuccessResponse(
            data={"document_id": doc.id},
            message="Document uploaded and processing started",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/documents", response_model=SuccessResponse)
async def upload_document(
    data: DocumentUpload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Legacy JSON-body upload endpoint (kept for backward compatibility)."""
    try:
        doc = await DocumentController.upload(
            db=db,
            workspace_id=workspace_id,
            user_id=current_user.id,
            name=data.name,
            file_type=data.file_type,
            file_url=data.file_url,
            background_tasks=background_tasks,
        )
        return SuccessResponse(
            data={"document_id": doc.id},
            message="Document uploaded and processing started",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/documents", response_model=SuccessResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    docs = await DocumentController.get_all(db=db, workspace_id=workspace_id)
    return SuccessResponse(
        data={"documents": [d.id for d in docs]}, message="Documents retrieved"
    )


@router.get("/documents/{document_id}", response_model=SuccessResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        doc = await DocumentController.get_by_id(db, document_id, workspace_id)
        return SuccessResponse(
            data={"id": doc.id, "name": doc.name, "status": doc.status, "file_type": doc.file_type},
            message="Document retrieved",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/documents/{document_id}", response_model=SuccessResponse)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        await DocumentController.delete(db, document_id, workspace_id)
        return SuccessResponse(data={"deleted": True}, message="Document deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/search", response_model=SuccessResponse)
async def search_knowledge(
    data: SearchQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    try:
        context_result = await DocumentController.search(
            db=db, workspace_id=workspace_id, query=data.query, limit=data.limit
        )
        return SuccessResponse(
            data=context_result, message="Search completed and context assembled"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
