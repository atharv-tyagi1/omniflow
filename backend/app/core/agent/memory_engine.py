"""Memory Engine — DB-backed retrieval of the 3-tier memory hierarchy.

Hierarchy (strict order, never mixed):
  WorkspaceMemory → AgentMemory → ConversationMemory
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.workspace_memory import WorkspaceMemory
from backend.app.models.agent_memory import AgentMemory
from backend.app.models.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)

# Maximum characters to include from each memory layer before truncation
_MAX_WORKSPACE_CHARS = 4_000
_MAX_AGENT_CHARS = 2_000
_MAX_CONVERSATION_TURNS = 20  # last N messages from conversation memory


class MemoryEngine:
    """
    Retrieves and updates memory layers (Workspace → Agent → Conversation)
    maintaining strict boundary separation.

    Never mixes layers. Never surfaces Workspace Memory from private conversations.
    """

    # ──────────────────────────────────────────────────────────────────────────
    # RETRIEVAL
    # ──────────────────────────────────────────────────────────────────────────

    async def get_workspace_memory(self, db: AsyncSession, workspace_id: UUID) -> str:
        """Retrieves shared business knowledge for the workspace, truncated to limit."""
        try:
            result = await db.execute(
                select(WorkspaceMemory)
                .where(WorkspaceMemory.workspace_id == workspace_id)
                .order_by(desc(WorkspaceMemory.updated_at))
                .limit(10)
            )
            rows = result.scalars().all()
            if not rows:
                return ""

            combined = "\n".join(r.content for r in rows)
            if len(combined) > _MAX_WORKSPACE_CHARS:
                combined = combined[:_MAX_WORKSPACE_CHARS] + "\n... [workspace memory truncated]"
            logger.debug(f"Loaded workspace memory for {workspace_id}: {len(combined)} chars")
            return combined
        except Exception as e:
            logger.warning(f"Failed to load workspace memory for {workspace_id}: {e}")
            return ""

    async def get_agent_memory(self, db: AsyncSession, agent_id: UUID, workspace_id: UUID) -> str:
        """Retrieves agent-specific long-term context, scoped to workspace."""
        try:
            result = await db.execute(
                select(AgentMemory)
                .where(
                    AgentMemory.agent_id == agent_id,
                    AgentMemory.workspace_id == workspace_id,
                )
                .order_by(desc(AgentMemory.updated_at))
                .limit(5)
            )
            rows = result.scalars().all()
            if not rows:
                return ""

            combined = "\n".join(r.content for r in rows)
            if len(combined) > _MAX_AGENT_CHARS:
                combined = combined[:_MAX_AGENT_CHARS] + "\n... [agent memory truncated]"
            logger.debug(f"Loaded agent memory for {agent_id}: {len(combined)} chars")
            return combined
        except Exception as e:
            logger.warning(f"Failed to load agent memory for {agent_id}: {e}")
            return ""

    async def get_conversation_memory(
        self, db: AsyncSession, conversation_id: UUID, workspace_id: UUID
    ) -> str:
        """Retrieves the sliding window of conversation messages."""
        try:
            result = await db.execute(
                select(ConversationMemory)
                .where(
                    ConversationMemory.conversation_id == conversation_id,
                    ConversationMemory.workspace_id == workspace_id,
                )
                .order_by(desc(ConversationMemory.created_at))
                .limit(_MAX_CONVERSATION_TURNS)
            )
            rows = result.scalars().all()
            if not rows:
                return ""

            # Reverse so oldest first
            rows = list(reversed(rows))
            lines = [f"{r.role.upper()}: {r.content}" for r in rows]
            combined = "\n".join(lines)
            logger.debug(
                f"Loaded {len(rows)} conversation turns for {conversation_id}"
            )
            return combined
        except Exception as e:
            logger.warning(f"Failed to load conversation memory for {conversation_id}: {e}")
            return ""

    async def compile_memory_context(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> tuple[str, List[str]]:
        """
        Compiles all memory layers into a single formatted context block.
        Returns (context_string, references_list) where references_list tracks
        what was loaded for the Decision Trace.
        """
        references: List[str] = []

        w_mem = await self.get_workspace_memory(db, workspace_id)
        a_mem = await self.get_agent_memory(db, agent_id, workspace_id)
        c_mem = await self.get_conversation_memory(db, conversation_id, workspace_id)

        parts: List[str] = []
        if w_mem:
            parts.append(f"Workspace Business Knowledge:\n{w_mem}")
            references.append(f"workspace_memory:{workspace_id}")
        if a_mem:
            parts.append(f"Agent-Specific Context:\n{a_mem}")
            references.append(f"agent_memory:{agent_id}")
        if c_mem:
            parts.append(f"Recent Conversation:\n{c_mem}")
            references.append(f"conversation_memory:{conversation_id}")

        return "\n\n".join(parts), references

    # ──────────────────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ──────────────────────────────────────────────────────────────────────────

    async def save_turn(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        conversation_id: UUID,
        user_message: str,
        assistant_message: str,
        token_metadata: Optional[dict] = None,
    ) -> None:
        """
        Persists the current turn (user + assistant) to ConversationMemory.
        Each message is an individual row (avoids write contention on large arrays).
        """
        try:
            user_row = ConversationMemory(
                workspace_id=workspace_id,
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                metadata_json=None,
            )
            assistant_row = ConversationMemory(
                workspace_id=workspace_id,
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_message,
                metadata_json=token_metadata,
            )
            db.add(user_row)
            db.add(assistant_row)
            await db.flush()
            logger.debug(f"Saved conversation turn for {conversation_id}")
        except Exception as e:
            logger.error(f"Failed to save conversation turn: {e}")
            raise
