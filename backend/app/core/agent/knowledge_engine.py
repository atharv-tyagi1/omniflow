"""Knowledge Engine — wraps KnowledgeService to inject RAG chunks into the execution pipeline."""

import logging
from typing import List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_MAX_KNOWLEDGE_CHARS = 6_000  # Max context window allocation for knowledge


class KnowledgeEngine:
    """
    Bridges the Agent Runtime to the existing OmniFlow RAG architecture.
    Reuses KnowledgeService.search_knowledge() — does NOT duplicate retrieval logic.
    Enforces workspace permission boundaries on every retrieval.
    """

    async def retrieve_knowledge(
        self,
        db: AsyncSession,
        query: str,
        workspace_id: UUID,
        limit: int = 5,
    ) -> Tuple[str, List[str]]:
        """
        Retrieves relevant knowledge chunks scoped strictly to the workspace.

        Returns:
            (formatted_context_string, references_list)
            references_list is used to populate the Decision Trace knowledge_references.
        """
        try:
            from backend.app.services.knowledge_service import KnowledgeService

            chunks = await KnowledgeService.search_knowledge(
                db=db,
                workspace_id=workspace_id,
                query=query,
                limit=limit,
            )

            if not chunks:
                logger.debug(f"No knowledge chunks found for query in workspace {workspace_id}")
                return "", []

            references: List[str] = []
            parts: List[str] = []

            for chunk in chunks:
                chunk_text = chunk.content if hasattr(chunk, "content") else str(chunk)
                doc_id = str(chunk.document_id) if hasattr(chunk, "document_id") else "unknown"
                chunk_idx = chunk.chunk_index if hasattr(chunk, "chunk_index") else 0

                parts.append(f"[Source: doc:{doc_id}, chunk:{chunk_idx}]\n{chunk_text}")
                references.append(f"doc:{doc_id}:chunk:{chunk_idx}")

            context = "\n\n".join(parts)

            # Truncate if oversized
            if len(context) > _MAX_KNOWLEDGE_CHARS:
                context = context[:_MAX_KNOWLEDGE_CHARS] + "\n... [knowledge context truncated]"

            logger.info(
                f"Retrieved {len(chunks)} knowledge chunks for workspace {workspace_id}"
            )
            return context, references

        except Exception as e:
            logger.warning(
                f"Knowledge retrieval failed for workspace {workspace_id}: {e}. "
                "Continuing without knowledge context."
            )
            return "", []
