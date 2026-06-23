from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import logging

from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.core.exceptions import NotFoundError
from backend.app.core.rag.parsers import DocumentParser
from backend.app.core.rag.chunker import RecursiveCharacterTextSplitter
from backend.app.core.ai.gemini_client import GeminiClient
from backend.app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class KnowledgeService:
    @staticmethod
    async def create_document(
        db: AsyncSession,
        workspace_id: UUID,
        user_id: UUID,
        name: str,
        file_type: str,
        file_url: str,
    ) -> Document:
        doc = await DocumentRepository.create(
            db=db,
            workspace_id=workspace_id,
            name=name,
            file_type=file_type,
            file_url=file_url,
            uploaded_by=user_id,
        )
        return doc

    @staticmethod
    async def process_document_task(
        document_id: UUID, workspace_id: UUID, file_url: str, file_type: str
    ):
        """
        Background task to download (or read locally), parse, chunk, embed, and store document data.
        Supports both http:// and file:// URL schemes.
        """
        async with AsyncSessionLocal() as db:
            try:
                # 1. Obtain raw bytes
                if file_url.startswith("file://"):
                    # Local file – strip the scheme and read from disk
                    local_path = file_url[len("file://"):]
                    with open(local_path, "rb") as fh:
                        file_bytes = fh.read()
                else:
                    # Remote file – fetch via HTTP
                    async with httpx.AsyncClient() as client:
                        response = await client.get(file_url)
                        response.raise_for_status()
                        file_bytes = response.content

                # 2. Parse file
                extracted_text = DocumentParser.parse(file_bytes, file_type)
                if not extracted_text:
                    raise ValueError("No text extracted from document")

                # 3. Chunk text
                chunker = RecursiveCharacterTextSplitter(
                    chunk_size=1000, chunk_overlap=200
                )
                text_chunks = chunker.split_text(extracted_text)

                # 4. Generate embeddings
                embeddings = GeminiClient.generate_embeddings(text_chunks)

                # 5. Store chunks
                db_chunks = []
                for idx, (text, emb) in enumerate(zip(text_chunks, embeddings)):
                    db_chunks.append(
                        {
                            "document_id": document_id,
                            "chunk_index": idx,
                            "content": text,
                            "embedding": emb,
                        }
                    )

                await DocumentRepository.add_chunks(db, db_chunks)

                # 6. Update Status
                await DocumentRepository.update_status(db, document_id, "ready")

            except Exception as e:
                logger.error(f"Failed to process document {document_id}: {e}")
                await DocumentRepository.update_status(db, document_id, "failed")

    @staticmethod
    async def get_document(
        db: AsyncSession, document_id: UUID, workspace_id: UUID
    ) -> Document:
        doc = await DocumentRepository.get_by_id(db, document_id, workspace_id)
        if not doc:
            raise NotFoundError("Document not found")
        return doc

    @staticmethod
    async def list_documents(db: AsyncSession, workspace_id: UUID) -> List[Document]:
        return await DocumentRepository.list_by_workspace(db, workspace_id)

    @staticmethod
    async def search_knowledge(
        db: AsyncSession, workspace_id: UUID, query: str, limit: int = 5
    ) -> List[DocumentChunk]:
        # Embed the incoming search query
        query_embedding = GeminiClient.embed_query(query)

        # Execute vector search
        return await DocumentRepository.search_similar_chunks(
            db=db, embedding=query_embedding, workspace_id=workspace_id, limit=limit
        )

    @staticmethod
    async def delete_document(
        db: AsyncSession, document_id: UUID, workspace_id: UUID
    ) -> bool:
        success = await DocumentRepository.delete(db, document_id, workspace_id)
        if not success:
            raise NotFoundError("Document not found")
        return success
