"""Agent Service — loads agent configuration from DB and dispatches to AgentRuntime."""

import uuid
import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.agent import Agent
from backend.app.models.agent_version import AgentVersion
from backend.app.models.agent_prompt import AgentPrompt
from backend.app.models.agent_model import AgentModel
from backend.app.models.agent_tool_policy import AgentToolPolicy
from backend.app.models.workspace_memory import WorkspaceMemory
from backend.app.models.conversation import Conversation
from backend.app.schemas.agent import AgentResponse
from backend.app.core.agent.engine import AgentRuntime

logger = logging.getLogger(__name__)


class AgentService:
    """
    Responsible for:
    1. Loading the published AgentVersion from the database
    2. Building the complete agent_config dict
    3. Dispatching to AgentRuntime.execute() with a live DB session

    All logic is configuration-driven. No agent-specific code exists here.
    """

    @staticmethod
    async def get_published_config(
        db: AsyncSession,
        workspace_id: UUID,
        category: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Loads the published AgentVersion for a given workspace and category.
        Returns None if no active agent with a published version is found.
        """
        # 1. Find the active Agent by workspace and category
        result = await db.execute(
            select(Agent)
            .where(
                Agent.workspace_id == workspace_id,
                Agent.category == category,
                Agent.is_active == True,
            )
        )
        agent = result.scalars().first()
        if not agent:
            logger.info(
                f"No active agent found for workspace={workspace_id} category={category}"
            )
            return None

        # 2. Find the published AgentVersion
        result = await db.execute(
            select(AgentVersion)
            .where(
                AgentVersion.agent_id == agent.id,
                AgentVersion.is_published == True,
            )
        )
        version = result.scalars().first()
        if not version:
            logger.info(f"No published version for agent {agent.id}")
            return None

        # 3. Load dependencies (Prompt, Model, ToolPolicies)
        prompt_res = await db.execute(
            select(AgentPrompt).where(AgentPrompt.version_id == version.id)
        )
        prompt = prompt_res.scalars().first()

        model_res = await db.execute(
            select(AgentModel).where(AgentModel.version_id == version.id)
        )
        model = model_res.scalars().first()

        tool_res = await db.execute(
            select(AgentToolPolicy).where(AgentToolPolicy.version_id == version.id)
        )
        tool_policies = tool_res.scalars().all()

        # 4. Build workspace policies string from WorkspaceMemory
        # (Policies can be stored as a tagged memory entry — looking for "policy" key)
        workspace_policy_str = "Respect all workspace rules and maintain professional conduct."

        # 5. Assemble configuration
        config: Dict[str, Any] = {
            # Identifiers
            "agent_id": str(agent.id),
            "version_id": str(version.id),
            "workspace_id": str(workspace_id),
            "agent_name": agent.name,
            "category": category,
            "is_public_allowed": agent.is_public_allowed,

            # Prompt
            "system_prompt": prompt.system_prompt if prompt else "You are a helpful AI assistant.",
            "welcome_prompt": prompt.welcome_prompt if prompt else "",
            "fallback_prompt": prompt.fallback_prompt if prompt else "",
            "agent_prompt": (
                f"Welcome: {prompt.welcome_prompt}\nFallback: {prompt.fallback_prompt}"
                if prompt and (prompt.welcome_prompt or prompt.fallback_prompt)
                else ""
            ),
            "prompt_version_id": str(prompt.id) if prompt else None,

            # Model
            "provider": model.provider if model else "gemini",
            "model": model.model_name if model else "gemini-2.0-flash",
            "temperature": (
                model.config.get("temperature", 0.7) if model and model.config else 0.7
            ),
            "max_tokens": (
                model.config.get("max_tokens") if model and model.config else None
            ),

            # Tools
            "tool_policies": [
                {
                    "tool_type": tp.tool_type,
                    "tool_config": tp.tool_config or {},
                    "allowed_inputs": tp.allowed_inputs,
                    "allowed_outputs": tp.allowed_outputs,
                    "rate_limit": tp.rate_limit,
                    "approval_required": tp.approval_required,
                }
                for tp in tool_policies
            ],

            # Workspace
            "workspace_policies": workspace_policy_str,
        }

        logger.info(
            f"Agent config loaded: agent={agent.name}({agent.id}) "
            f"version={version.id} provider={config['provider']} model={config['model']}"
        )
        return config

    @staticmethod
    async def get_config_by_agent_id(
        db: AsyncSession,
        agent_id: UUID,
        workspace_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Loads published config by agent_id (for direct agent API access).
        Enforces workspace ownership before returning config.
        """
        result = await db.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.workspace_id == workspace_id,  # TENANT ISOLATION
                Agent.is_active == True,
            )
        )
        agent = result.scalars().first()
        if not agent:
            return None

        return await AgentService.get_published_config(db, workspace_id, agent.category)

    @staticmethod
    async def dispatch(
        db: AsyncSession,
        workspace_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        user_message: str,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main dispatch method — loads agent config and calls AgentRuntime.execute().
        All memory, knowledge, tool execution, and telemetry happen inside the runtime.
        """
        # Load config by agent_id first, fall back to category lookup
        agent_config = await AgentService.get_config_by_agent_id(db, agent_id, workspace_id)

        # Auto-create a conversation record if none provided (satisfies FK constraint on agent_runs)
        existing_conv = None
        if conversation_id:
            conv_res = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            existing_conv = conv_res.scalars().first()

        if not existing_conv:
            new_conv = Conversation(
                id=conversation_id or uuid.uuid4(),
                workspace_id=workspace_id,
                channel_id=None,
                status="active",
                handoff_status="none",
            )
            db.add(new_conv)
            await db.flush()
            conversation_id = new_conv.id

        if not agent_config and category:
            agent_config = await AgentService.get_published_config(db, workspace_id, category)

        if not agent_config:
            logger.warning(
                f"No agent config found for agent_id={agent_id} workspace={workspace_id} "
                f"category={category}. Using default fallback config."
            )
            # Graceful fallback — minimal config
            agent_config = {
                "agent_id": str(agent_id),
                "version_id": str(uuid.uuid4()),
                "workspace_id": str(workspace_id),
                "agent_name": "Assistant",
                "category": category or "general",
                "system_prompt": "You are a helpful AI assistant for this workspace.",
                "agent_prompt": "",
                "provider": "gemini",
                "model": "gemini-2.0-flash",
                "temperature": 0.7,
                "tool_policies": [],
                "workspace_policies": "",
                "is_public_allowed": False,
            }

        runtime = AgentRuntime()
        result = await runtime.execute(
            db=db,
            workspace_id=workspace_id,
            agent_id=agent_id,
            version_id=UUID(agent_config["version_id"]),
            conversation_id=conversation_id,
            user_message=user_message,
            agent_config=agent_config,
            workspace_policies=agent_config.get("workspace_policies", ""),
            is_public_allowed=agent_config.get("is_public_allowed", False),
        )
        return result

    @staticmethod
    async def dispatch_agent(
        db: AsyncSession,
        workspace_id: UUID,
        category: str,
        query: str,
        router_metadata: dict,
        conversation_id: UUID,
        customer_id: UUID,
        bounded_context: Optional[dict] = None,
    ) -> AgentResponse:
        """
        Legacy compatibility method — wraps dispatch() and returns AgentResponse.
        Used by the existing conversation router.
        Falls back to legacy AgentFactory if no DB config is found.
        """
        agent_config = await AgentService.get_published_config(db, workspace_id, category)
        merged_metadata = {**router_metadata, **(bounded_context or {})}

        if agent_config:
            # ── NEW PATH: DB-configured agent through AgentRuntime ──
            runtime = AgentRuntime()
            result = await runtime.execute(
                db=db,
                workspace_id=workspace_id,
                agent_id=UUID(agent_config["agent_id"]),
                version_id=UUID(agent_config["version_id"]),
                conversation_id=conversation_id,
                user_message=query,
                agent_config=agent_config,
                workspace_policies=agent_config.get("workspace_policies", ""),
                is_public_allowed=agent_config.get("is_public_allowed", False),
            )
            return AgentResponse(
                content=result.get("content", ""),
                confidence=1.0 if result.get("status") == "success" else 0.5,
                agent_name=agent_config.get("agent_name", category),
                sentiment="neutral",
                handoff_recommended=False,
                requires_human=False,
            )
        else:
            # ── LEGACY FALLBACK: rule-based agents ──
            logger.info(f"No DB config for category={category} — using legacy AgentFactory")
            from backend.app.agents.factory import AgentFactory
            target_agent = AgentFactory.create_agent(category)
            return await target_agent.respond(
                db=db,
                conversation_id=conversation_id,
                customer_id=customer_id,
                workspace_id=workspace_id,
                query=query,
                router_metadata=merged_metadata,
            )

    # ──────────────────────────────────────────────────────────────────────────
    # LEGACY: get_active_config (backward compat for existing code)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def get_active_config(
        db: AsyncSession,
        workspace_id: UUID,
        category: str,
    ) -> Optional[Dict[str, Any]]:
        """Backward-compatible alias for get_published_config."""
        return await AgentService.get_published_config(db, workspace_id, category)
