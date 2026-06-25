from uuid import UUID
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.rag_service import RagService
from backend.app.core.agent.exceptions import ContextAssemblyError

class KnowledgeEngine:
    """
    Wraps RagService to inject knowledge chunks into the execution pipeline,
    validating workspace permissions implicitly through RagService.
    """

    @staticmethod
    async def retrieve_knowledge(
        db: AsyncSession, 
        workspace_id: UUID, 
        query: str, 
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieves knowledge chunks.
        
        Returns:
            Dict containing:
                - "context_string": Formatted chunk text
                - "sources": List of source dicts
        """
        if not query:
            return {"context_string": "", "sources": []}
            
        try:
            return await RagService.build_context(db, workspace_id, query, limit)
        except Exception as e:
            raise ContextAssemblyError(f"Failed to retrieve knowledge context: {str(e)}")
