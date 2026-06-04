from uuid import UUID
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.knowledge_service import KnowledgeService


class RagService:
    """
    Context Assembly Service for the RAG Pipeline.
    Responsible for fetching relevant chunks and assembling them into a format
    ready for LLM prompt injection, including source attribution.
    """

    @staticmethod
    async def build_context(
        db: AsyncSession, workspace_id: UUID, query: str, limit: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieves top relevant chunks and formats them into a context string.
        """
        chunks = await KnowledgeService.search_knowledge(db, workspace_id, query, limit)

        if not chunks:
            return {
                "context_string": "",
                "sources": []
            }

        context_parts = []
        sources = []

        # Assuming `document` relationship is eager loaded in Repository
        for chunk in chunks:
            doc_name = chunk.document.name if chunk.document else "Unknown Document"
            doc_id = str(chunk.document_id)
            
            # Format: [Source: Document Name (Chunk X)]
            attribution_header = f"[Source: {doc_name} (Chunk {chunk.chunk_index})]"
            context_parts.append(f"{attribution_header}\n{chunk.content}")
            
            if doc_id not in [s["document_id"] for s in sources]:
                sources.append({
                    "document_id": doc_id,
                    "document_name": doc_name
                })

        return {
            "context_string": "\n\n---\n\n".join(context_parts),
            "sources": sources
        }
