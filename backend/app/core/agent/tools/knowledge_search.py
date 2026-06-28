"""Knowledge Search Tool — reuses existing KnowledgeService RAG retrieval."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


async def search_knowledge(
    query: str,
    workspace_id: str,
    limit: int = 5,
    db: Any = None,
) -> Dict[str, Any]:
    """
    Searches the workspace knowledge base using the existing RAG infrastructure.
    Enforces workspace-scoped retrieval — never returns cross-workspace data.
    """
    if not query or not workspace_id:
        return {"status": "error", "message": "query and workspace_id are required"}

    if db is None:
        from backend.app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            return await _search(session, query, workspace_id, limit)

    return await _search(db, query, workspace_id, limit)


async def _search(db: Any, query: str, workspace_id: str, limit: int) -> Dict[str, Any]:
    try:
        from backend.app.services.knowledge_service import KnowledgeService

        chunks = await KnowledgeService.search_knowledge(
            db=db,
            workspace_id=UUID(workspace_id),
            query=query,
            limit=limit,
        )

        results = []
        for chunk in chunks:
            results.append({
                "content": chunk.content,
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
            })

        logger.info(f"Knowledge search returned {len(results)} chunks for workspace {workspace_id}")
        return {
            "status": "success",
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Knowledge search failed for workspace {workspace_id}: {e}")
        return {"status": "error", "message": str(e), "results": []}
