from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.schemas.agent import AgentContext

class AgentContextBuilder:
    """Aggregates multi-modal context into a structured AgentContext object."""

    @staticmethod
    async def build_context(
        db: AsyncSession,
        conversation_id: UUID,
        customer_id: UUID,
        workspace_id: UUID,
        query: str,
        router_metadata: dict
    ) -> AgentContext:
        """
        Gathers conversation history, RAG context, workspace info, customer profile,
        and current state to supply to the prompt builder.
        """
        # Placeholder implementations for future integration
        # Future phases will fetch real DB models here
        conversation_history = []
        rag_context = []
        workspace_context = {"id": str(workspace_id)}
        customer_context = {"id": str(customer_id)}
        conversation_state = {"status": "active"}

        return AgentContext(
            conversation_history=conversation_history,
            rag_context=rag_context,
            workspace_context=workspace_context,
            customer_context=customer_context,
            conversation_state=conversation_state,
            router_metadata=router_metadata,
        )
