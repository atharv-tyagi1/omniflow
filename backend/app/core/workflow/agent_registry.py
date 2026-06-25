"""Agent Registry for Workflow Engine."""

from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.agent import Agent


class AgentRegistry:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_agent(self, workspace_id: UUID, agent_id: UUID) -> Optional[Dict[str, Any]]:
        """Fetch agent metadata from the database dynamically."""
        stmt = select(Agent).where(Agent.id == agent_id, Agent.workspace_id == workspace_id, Agent.status == "active")
        result = await self.session.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            return None
            
        return {
            "id": str(agent.id),
            "name": agent.name,
            "capabilities": agent.capabilities,
            "description": agent.description,
        }
