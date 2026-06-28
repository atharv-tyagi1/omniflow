import uuid
import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.agent import Agent
from backend.app.models.agent_version import AgentVersion
from backend.app.core.exceptions import ConflictError, NotFoundError

logger = logging.getLogger(__name__)

class AgentLifecycleService:
    """Handles agent lifecycle (Clone, Archive, Restore, Delete, Draft selection)."""

    @staticmethod
    async def get_draft_version(db: AsyncSession, agent_id: UUID, workspace_id: UUID) -> AgentVersion:
        """
        Canonical draft-selection rule.
        Finds the highest version number that is not published.
        If all are published, creates a new draft version.
        """
        # Ensure agent belongs to workspace
        res = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.workspace_id == workspace_id))
        agent = res.scalars().first()
        if not agent:
            raise NotFoundError("Agent not found")

        # Find draft
        v_res = await db.execute(
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id, AgentVersion.is_published == False)
            .order_by(AgentVersion.version_number.desc())
        )
        draft = v_res.scalars().first()

        if draft:
            return draft

        # No draft exists, create one from highest version
        v_res = await db.execute(
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent_id)
            .order_by(AgentVersion.version_number.desc())
        )
        highest = v_res.scalars().first()
        next_ver = highest.version_number + 1 if highest else 1

        new_draft = AgentVersion(
            id=uuid.uuid4(),
            agent_id=agent_id,
            version_number=next_ver,
            is_published=False
        )
        db.add(new_draft)
        await db.flush()
        return new_draft

    @staticmethod
    async def publish_version(db: AsyncSession, agent_id: UUID, workspace_id: UUID, version_id: UUID) -> AgentVersion:
        """Idempotent publish operation."""
        # Ensure agent ownership
        res = await db.execute(select(Agent).where(Agent.id == agent_id, Agent.workspace_id == workspace_id))
        if not res.scalars().first():
            raise NotFoundError("Agent not found")

        v_res = await db.execute(select(AgentVersion).where(AgentVersion.id == version_id, AgentVersion.agent_id == agent_id))
        target = v_res.scalars().first()
        if not target:
            raise NotFoundError("Version not found")

        if target.is_published:
            return target # Idempotent

        # Unpublish all others
        await db.execute(
            AgentVersion.__table__.update()
            .where(AgentVersion.agent_id == agent_id)
            .values(is_published=False)
        )

        target.is_published = True
        await db.commit()
        await db.refresh(target)
        return target
