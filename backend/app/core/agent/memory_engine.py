from uuid import UUID
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.workspace_memory import WorkspaceMemory
from backend.app.models.agent_memory import AgentMemory
from backend.app.models.conversation_memory import ConversationMemory
from backend.app.core.agent.exceptions import ContextAssemblyError

class MemoryEngine:
    """
    Retrieves and updates memory layers (Workspace -> Agent -> Conversation)
    maintaining strict separation between them.
    """

    @staticmethod
    async def get_workspace_memory(db: AsyncSession, workspace_id: UUID) -> List[str]:
        stmt = select(WorkspaceMemory).where(WorkspaceMemory.workspace_id == workspace_id)
        result = await db.execute(stmt)
        memories = result.scalars().all()
        return [m.content for m in memories]

    @staticmethod
    async def get_agent_memory(db: AsyncSession, agent_id: UUID) -> List[str]:
        stmt = select(AgentMemory).where(AgentMemory.agent_id == agent_id)
        result = await db.execute(stmt)
        memories = result.scalars().all()
        return [m.content for m in memories]

    @staticmethod
    async def get_conversation_memory(db: AsyncSession, conversation_id: UUID) -> List[str]:
        stmt = select(ConversationMemory).where(ConversationMemory.conversation_id == conversation_id)
        result = await db.execute(stmt)
        memories = result.scalars().all()
        return [m.content for m in memories]

    @staticmethod
    async def assemble_memory_context(
        db: AsyncSession, 
        workspace_id: UUID, 
        agent_id: UUID, 
        conversation_id: UUID
    ) -> Dict[str, str]:
        """
        Retrieves all memory layers and formats them.
        """
        try:
            workspace_mem = await MemoryEngine.get_workspace_memory(db, workspace_id)
            agent_mem = await MemoryEngine.get_agent_memory(db, agent_id)
            conv_mem = await MemoryEngine.get_conversation_memory(db, conversation_id)

            return {
                "workspace_memory": "\n".join(workspace_mem),
                "agent_memory": "\n".join(agent_mem),
                "conversation_memory": "\n".join(conv_mem)
            }
        except Exception as e:
            raise ContextAssemblyError(f"Failed to retrieve memory layers: {str(e)}")
