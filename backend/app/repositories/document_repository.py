from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional, List, Dict, Any

from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk
from pgvector.sqlalchemy import Vector


class DocumentRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        name: str,
        file_type: str,
        file_url: str,
        uploaded_by: UUID
    ) -> Document:
        db_obj = Document(
            workspace_id=workspace_id,
            name=name,
            file_type=file_type,
            file_url=file_url,
            uploaded_by=uploaded_by
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_id(db: AsyncSession, document_id: UUID, workspace_id: UUID) -> Optional[Document]:
        result = await db.execute(
            select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_workspace(db: AsyncSession, workspace_id: UUID) -> List[Document]:
        result = await db.execute(
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_status(db: AsyncSession, document_id: UUID, status: str) -> Optional[Document]:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalars().first()
        if doc:
            doc.status = status
            db.add(doc)
            await db.flush()
        return doc

    @staticmethod
    async def add_chunks(db: AsyncSession, chunks: List[Dict[str, Any]]) -> None:
        db_chunks = [
            DocumentChunk(
                document_id=c["document_id"],
                chunk_index=c["chunk_index"],
                content=c["content"],
                embedding=c["embedding"]
            )
            for c in chunks
        ]
        db.add_all(db_chunks)
        await db.flush()

    @staticmethod
    async def search_similar_chunks(
        db: AsyncSession, 
        embedding: List[float], 
        workspace_id: UUID,
        limit: int = 5
    ) -> List[DocumentChunk]:
        # Using L2 distance operator `<->` from pgvector
        # Requires joining with documents to enforce workspace isolation
        stmt = (
            select(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.workspace_id == workspace_id)
            .order_by(DocumentChunk.embedding.l2_distance(embedding))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
