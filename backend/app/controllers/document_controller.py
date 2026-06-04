from fastapi import BackgroundTasks
from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.knowledge_service import KnowledgeService
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk


class DocumentController:
    @staticmethod
    async def upload(
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        name: str,
        file_type: str,
        file_url: str,
        background_tasks: BackgroundTasks,
    ) -> Document:
        doc = await KnowledgeService.create_document(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            name=name,
            file_type=file_type,
            file_url=file_url,
        )

        # Dispatch heavy RAG ingestion workload
        background_tasks.add_task(
            KnowledgeService.process_document_task,
            document_id=doc.id,
            workspace_id=workspace_id,
            file_url=file_url,
            file_type=file_type,
        )
        return doc

    @staticmethod
    async def get_all(db: AsyncSession, workspace_id: UUID) -> List[Document]:
        return await KnowledgeService.list_documents(db, workspace_id)

    @staticmethod
    async def get_by_id(
        db: AsyncSession, document_id: UUID, workspace_id: UUID
    ) -> Document:
        return await KnowledgeService.get_document(db, document_id, workspace_id)

    @staticmethod
    async def delete(db: AsyncSession, document_id: UUID, workspace_id: UUID) -> bool:
        return await KnowledgeService.delete_document(db, document_id, workspace_id)

    @staticmethod
    async def search(
        db: AsyncSession, workspace_id: UUID, query: str, limit: int = 5
    ) -> dict:
        from backend.app.services.rag_service import RagService
        return await RagService.build_context(db, workspace_id, query, limit)
