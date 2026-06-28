"""
Phase 21.2F — Agent Platform API Router
Workspace-scoped private endpoints for full agent lifecycle and runtime.
"""
import uuid
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User as UserResponse
from backend.app.schemas.agent_builder import (
    AgentListResponse,
    AgentDetailResponse,
    AgentCreateRequest,
    AgentVersionCreateRequest,
    AgentVersionResponse,
    AgentPromptConfig,
    AgentModelConfig,
    AgentChatRequest,
    AgentChatResponse,
    AgentRunSummary,
    AgentRunDetail,
    AgentRunListResponse,
    ToolPolicyRequest,
    ToolPolicyResponse,
    ToolPolicyListResponse,
    AgentPublishRequest,
    AgentCloneRequest,
    SandboxExecuteRequest,
)
from backend.app.models.agent import Agent
from backend.app.models.agent_version import AgentVersion
from backend.app.models.agent_prompt import AgentPrompt
from backend.app.models.agent_model import AgentModel
from backend.app.models.agent_tool_policy import AgentToolPolicy
from backend.app.models.agent_run import AgentRun
from backend.app.models.agent_run_step import AgentRunStep
from backend.app.models.agent_decision_trace import AgentDecisionTrace
from backend.app.services.agent_service import AgentService
from backend.app.services.agent_lifecycle_service import AgentLifecycleService
from backend.app.core.exceptions import NotFoundError, WorkspaceIsolationError

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

async def _get_agent_or_404(db: AsyncSession, agent_id: uuid.UUID, workspace_id: uuid.UUID) -> Agent:
    """Load an agent, enforcing workspace ownership."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.workspace_id == workspace_id)
    )
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


async def _build_chat_response(result: Dict[str, Any], conversation_id: uuid.UUID) -> AgentChatResponse:
    return AgentChatResponse(
        request_id=result.get("request_id", ""),
        content=result.get("content", ""),
        status=result.get("status", "success"),
        run_id=uuid.UUID(result["run_id"]) if result.get("run_id") else None,
        conversation_id=conversation_id,
        latency_ms=result.get("latency_ms", 0),
        tokens_used=result.get("tokens_used", 0),
        knowledge_used=result.get("knowledge_used", False),
        memory_used=result.get("memory_used", False),
        tool_calls=result.get("tool_calls", []),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. AGENT MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[AgentListResponse])
@router.get("/", response_model=List[AgentListResponse], include_in_schema=False)
async def list_agents(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """List all agents for a workspace."""
    result = await db.execute(select(Agent).where(Agent.workspace_id == workspace_id))
    agents = result.scalars().all()

    responses = []
    for agent in agents:
        v_result = await db.execute(
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent.id, AgentVersion.is_published == True)
            .order_by(AgentVersion.version_number.desc())
            .limit(1)
        )
        active_v = v_result.scalars().first()
        responses.append(
            AgentListResponse(
                id=agent.id,
                name=agent.name,
                category=agent.category,
                is_active=agent.is_active,
                created_at=agent.created_at,
                active_version_id=active_v.id if active_v else None,
            )
        )
    return responses


@router.post("", response_model=AgentListResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AgentListResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_agent(
    workspace_id: uuid.UUID,
    request: AgentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new agent."""
    new_agent = Agent(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        name=request.name,
        category=request.category,
        is_active=request.is_active,
    )
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)

    return AgentListResponse(
        id=new_agent.id,
        name=new_agent.name,
        category=new_agent.category,
        is_active=new_agent.is_active,
        created_at=new_agent.created_at,
        active_version_id=None,
    )


@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent_detail(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get details of a specific agent, including all its versions."""
    agent = await _get_agent_or_404(db, agent_id, workspace_id)

    versions_result = await db.execute(
        select(AgentVersion)
        .where(AgentVersion.agent_id == agent_id)
        .order_by(AgentVersion.version_number.desc())
    )
    versions = versions_result.scalars().all()

    version_responses = []
    active_version_id = None

    for v in versions:
        if v.is_published and not active_version_id:
            active_version_id = v.id

        p_result = await db.execute(select(AgentPrompt).where(AgentPrompt.version_id == v.id))
        prompt_record = p_result.scalars().first()

        m_result = await db.execute(select(AgentModel).where(AgentModel.version_id == v.id))
        model_record = m_result.scalars().first()

        version_responses.append(
            AgentVersionResponse(
                id=v.id,
                version_number=v.version_number,
                is_published=v.is_published,
                created_at=v.created_at,
                prompt=AgentPromptConfig(
                    system_prompt=prompt_record.system_prompt,
                    welcome_prompt=prompt_record.welcome_prompt,
                    fallback_prompt=prompt_record.fallback_prompt,
                ) if prompt_record else None,
                model=AgentModelConfig(
                    provider=model_record.provider,
                    model_name=model_record.model_name,
                    config=model_record.config,
                ) if model_record else None,
            )
        )

    return AgentDetailResponse(
        id=agent.id,
        name=agent.name,
        category=agent.category,
        is_active=agent.is_active,
        created_at=agent.created_at,
        active_version_id=active_version_id,
        versions=version_responses,
    )


@router.patch("/{agent_id}", response_model=AgentListResponse)
async def update_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    request: AgentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update agent metadata."""
    agent = await _get_agent_or_404(db, agent_id, workspace_id)
    agent.name = request.name
    agent.category = request.category
    agent.is_active = request.is_active
    await db.commit()
    await db.refresh(agent)
    return AgentListResponse(
        id=agent.id,
        name=agent.name,
        category=agent.category,
        is_active=agent.is_active,
        created_at=agent.created_at,
        active_version_id=None,
    )


@router.post("/{agent_id}/archive", response_model=AgentListResponse)
async def archive_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Archive (soft-delete) an agent."""
    agent = await _get_agent_or_404(db, agent_id, workspace_id)
    agent.is_active = False
    await db.commit()
    await db.refresh(agent)
    return AgentListResponse(
        id=agent.id, name=agent.name, category=agent.category,
        is_active=agent.is_active, created_at=agent.created_at, active_version_id=None,
    )


@router.post("/{agent_id}/restore", response_model=AgentListResponse)
async def restore_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Restore an archived agent."""
    agent = await _get_agent_or_404(db, agent_id, workspace_id)
    agent.is_active = True
    await db.commit()
    await db.refresh(agent)
    return AgentListResponse(
        id=agent.id, name=agent.name, category=agent.category,
        is_active=agent.is_active, created_at=agent.created_at, active_version_id=None,
    )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Permanently delete an agent and all versions."""
    agent = await _get_agent_or_404(db, agent_id, workspace_id)
    await db.delete(agent)
    await db.commit()


@router.post("/{agent_id}/clone", response_model=AgentListResponse, status_code=status.HTTP_201_CREATED)
async def clone_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    request: AgentCloneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Clone an existing agent into a new draft agent."""
    source = await _get_agent_or_404(db, agent_id, workspace_id)
    cloned = Agent(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        name=request.new_name,
        category=request.category or source.category,
        is_active=True,
    )
    db.add(cloned)
    await db.commit()
    await db.refresh(cloned)
    logger.info(f"Agent {agent_id} cloned to {cloned.id} in workspace {workspace_id}")
    return AgentListResponse(
        id=cloned.id, name=cloned.name, category=cloned.category,
        is_active=cloned.is_active, created_at=cloned.created_at, active_version_id=None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. VERSION MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{agent_id}/versions", response_model=AgentVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_version(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    request: AgentVersionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new version for an agent with prompt and model configs."""
    await _get_agent_or_404(db, agent_id, workspace_id)

    v_result = await db.execute(
        select(AgentVersion)
        .where(AgentVersion.agent_id == agent_id)
        .order_by(AgentVersion.version_number.desc())
        .limit(1)
    )
    last_v = v_result.scalars().first()
    next_number = (last_v.version_number + 1) if last_v else 1

    if request.publish:
        await db.execute(
            AgentVersion.__table__.update()
            .where(AgentVersion.agent_id == agent_id)
            .values(is_published=False)
        )

    new_version = AgentVersion(
        id=uuid.uuid4(),
        agent_id=agent_id,
        version_number=next_number,
        is_published=request.publish,
    )
    db.add(new_version)
    await db.flush()

    db.add(AgentPrompt(
        id=uuid.uuid4(), version_id=new_version.id,
        system_prompt=request.prompt.system_prompt,
        welcome_prompt=request.prompt.welcome_prompt,
        fallback_prompt=request.prompt.fallback_prompt,
    ))
    db.add(AgentModel(
        id=uuid.uuid4(), version_id=new_version.id,
        provider=request.model.provider,
        model_name=request.model.model_name,
        config=request.model.config,
    ))

    await db.commit()
    await db.refresh(new_version)

    return AgentVersionResponse(
        id=new_version.id, version_number=new_version.version_number,
        is_published=new_version.is_published, created_at=new_version.created_at,
        prompt=request.prompt, model=request.model,
    )


@router.post("/{agent_id}/versions/{version_id}/publish", response_model=AgentVersionResponse)
async def publish_agent_version(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Publish a specific version (idempotent — unpublishes all others)."""
    version = await AgentLifecycleService.publish_version(db, agent_id, workspace_id, version_id)

    p_res = await db.execute(select(AgentPrompt).where(AgentPrompt.version_id == version.id))
    prompt = p_res.scalars().first()

    m_res = await db.execute(select(AgentModel).where(AgentModel.version_id == version.id))
    model = m_res.scalars().first()

    return AgentVersionResponse(
        id=version.id, version_number=version.version_number,
        is_published=version.is_published, created_at=version.created_at,
        prompt=AgentPromptConfig(
            system_prompt=prompt.system_prompt,
            welcome_prompt=prompt.welcome_prompt,
            fallback_prompt=prompt.fallback_prompt,
        ) if prompt else None,
        model=AgentModelConfig(
            provider=model.provider, model_name=model.model_name, config=model.config,
        ) if model else None,
    )


@router.post("/{agent_id}/versions/{version_id}/rollback", response_model=AgentVersionResponse)
async def rollback_agent_version(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Rollback to a specific version (re-publishes it)."""
    # Rollback is idempotent publish on a historical version
    return await publish_agent_version(workspace_id, agent_id, version_id, db, current_user)


@router.get("/{agent_id}/versions", response_model=List[AgentVersionResponse])
async def list_agent_versions(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """List all versions of an agent."""
    await _get_agent_or_404(db, agent_id, workspace_id)
    result = await db.execute(
        select(AgentVersion)
        .where(AgentVersion.agent_id == agent_id)
        .order_by(AgentVersion.version_number.desc())
    )
    versions = result.scalars().all()
    response = []
    for v in versions:
        response.append(AgentVersionResponse(
            id=v.id, version_number=v.version_number,
            is_published=v.is_published, created_at=v.created_at,
        ))
    return response


# ─────────────────────────────────────────────────────────────────────────────
# 3. TOOL POLICIES
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{agent_id}/versions/{version_id}/tool-policies", response_model=ToolPolicyResponse)
async def create_tool_policy(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    version_id: uuid.UUID,
    request: ToolPolicyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Add a tool policy to a version."""
    v_res = await db.execute(
        select(AgentVersion).join(Agent).where(
            AgentVersion.id == version_id,
            Agent.id == agent_id,
            Agent.workspace_id == workspace_id,
        )
    )
    if not v_res.scalars().first():
        raise HTTPException(status_code=404, detail="Version not found")

    policy = AgentToolPolicy(
        id=uuid.uuid4(), version_id=version_id,
        tool_type=request.tool_type, tool_config=request.tool_config,
        allowed_inputs=request.allowed_inputs, allowed_outputs=request.allowed_outputs,
        rate_limit=request.rate_limit, approval_required=request.approval_required,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)

    return ToolPolicyResponse(
        id=policy.id, version_id=policy.version_id, tool_type=policy.tool_type,
        tool_config=policy.tool_config, allowed_inputs=policy.allowed_inputs,
        allowed_outputs=policy.allowed_outputs, rate_limit=policy.rate_limit,
        approval_required=policy.approval_required,
    )


@router.get("/{agent_id}/versions/{version_id}/tool-policies", response_model=ToolPolicyListResponse)
async def list_tool_policies(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """List all tool policies for a version."""
    v_res = await db.execute(
        select(AgentVersion).join(Agent).where(
            AgentVersion.id == version_id,
            Agent.id == agent_id,
            Agent.workspace_id == workspace_id,
        )
    )
    if not v_res.scalars().first():
        raise HTTPException(status_code=404, detail="Version not found")

    result = await db.execute(select(AgentToolPolicy).where(AgentToolPolicy.version_id == version_id))
    policies = result.scalars().all()

    return ToolPolicyListResponse(policies=[
        ToolPolicyResponse(
            id=p.id, version_id=p.version_id, tool_type=p.tool_type,
            tool_config=p.tool_config, allowed_inputs=p.allowed_inputs,
            allowed_outputs=p.allowed_outputs, rate_limit=p.rate_limit,
            approval_required=p.approval_required,
        )
        for p in policies
    ])


# ─────────────────────────────────────────────────────────────────────────────
# 4. RUNTIME — PRIVATE WORKSPACE EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{agent_id}/execute", response_model=AgentChatResponse)
async def execute_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Execute a single production turn with the published agent."""
    conversation_id = request.conversation_id or uuid.uuid4()

    result = await AgentService.dispatch(
        db=db,
        workspace_id=workspace_id,
        agent_id=agent_id,
        conversation_id=conversation_id,
        user_message=request.message,
    )
    return await _build_chat_response(result, conversation_id)


@router.post("/{agent_id}/execute/stream")
async def execute_agent_stream(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    request: AgentChatRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """SSE streaming execution with disconnect cancellation and heartbeat."""

    async def sse_generator() -> AsyncGenerator[str, None]:
        conversation_id = request.conversation_id or uuid.uuid4()
        heartbeat_interval = 15  # seconds

        async def heartbeat():
            while True:
                await asyncio.sleep(heartbeat_interval)
                yield f"event: heartbeat\ndata: {{}}\n\n"

        try:
            # Send opening event
            yield f"event: start\ndata: {json.dumps({'conversation_id': str(conversation_id)})}\n\n"

            # Run the agent dispatch (cancellable via task)
            task = asyncio.create_task(AgentService.dispatch(
                db=db,
                workspace_id=workspace_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                user_message=request.message,
            ))

            # Poll for client disconnect while waiting
            while not task.done():
                if await http_request.is_disconnected():
                    task.cancel()
                    logger.info(f"SSE client disconnected for agent {agent_id}, run cancelled.")
                    return
                yield f"event: heartbeat\ndata: {{}}\n\n"
                await asyncio.sleep(5)

            result = await task
            yield f"event: chunk\ndata: {json.dumps({'content': result.get('content', '')})}\n\n"
            yield f"event: done\ndata: {json.dumps({'status': result.get('status', 'success'), 'tokens_used': result.get('tokens_used', 0), 'latency_ms': result.get('latency_ms', 0)})}\n\n"

        except asyncio.CancelledError:
            yield f"event: cancelled\ndata: {json.dumps({'reason': 'client_disconnect'})}\n\n"
        except Exception as e:
            logger.error(f"SSE stream error for agent {agent_id}: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. SANDBOX — DRAFT EXECUTION (agent_manager+ only)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{agent_id}/sandbox")
async def get_sandbox_metadata(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get the current draft version metadata for sandbox inspection."""
    await _get_agent_or_404(db, agent_id, workspace_id)
    draft = await AgentLifecycleService.get_draft_version(db, agent_id, workspace_id)

    p_res = await db.execute(select(AgentPrompt).where(AgentPrompt.version_id == draft.id))
    prompt = p_res.scalars().first()

    return {
        "draft_version_id": str(draft.id),
        "version_number": draft.version_number,
        "is_published": draft.is_published,
        "system_prompt": prompt.system_prompt if prompt else None,
    }


@router.post("/{agent_id}/sandbox/execute", response_model=AgentChatResponse)
async def execute_sandbox_agent(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    request: SandboxExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Execute a test turn against the draft version (sandbox). Requires agent_manager+."""
    conversation_id = request.conversation_id or uuid.uuid4()

    result = await AgentService.dispatch(
        db=db,
        workspace_id=workspace_id,
        agent_id=agent_id,
        conversation_id=conversation_id,
        user_message=request.message,
    )
    return await _build_chat_response(result, conversation_id)


# ─────────────────────────────────────────────────────────────────────────────
# 6. EXECUTION HISTORY & DECISION TRACES
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{agent_id}/runs", response_model=AgentRunListResponse)
async def list_agent_runs(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """List recent runs for an agent."""
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.agent_id == agent_id, AgentRun.workspace_id == workspace_id)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()

    return AgentRunListResponse(runs=[
        AgentRunSummary(
            id=r.id, status=r.status,
            created_at=r.created_at, completed_at=r.completed_at,
            conversation_id=r.conversation_id,
        )
        for r in runs
    ])


@router.get("/{agent_id}/runs/{run_id}", response_model=AgentRunDetail)
async def get_agent_run_detail(
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """Get detailed execution trace for a single run."""
    result = await db.execute(
        select(AgentRun).where(
            AgentRun.id == run_id,
            AgentRun.workspace_id == workspace_id,
            AgentRun.agent_id == agent_id,
        )
    )
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    steps_result = await db.execute(
        select(AgentRunStep)
        .where(AgentRunStep.run_id == run_id)
        .order_by(AgentRunStep.created_at.asc())
    )
    steps = steps_result.scalars().all()

    step_list = []
    decision_trace = None

    for s in steps:
        step_list.append({
            "id": str(s.id),
            "type": s.step_type,
            "latency_ms": s.latency_ms,
            "payload": s.payload,
        })
        if s.step_type == "llm_call" and not decision_trace:
            trace_res = await db.execute(
                select(AgentDecisionTrace).where(AgentDecisionTrace.run_step_id == s.id)
            )
            t = trace_res.scalars().first()
            if t:
                decision_trace = {
                    "id": str(t.id),
                    "model_used": t.model_used,
                    "cost_tokens": t.cost_tokens,
                    "latency_ms": t.latency_ms,
                    "memory_references": t.memory_references,
                    "knowledge_references": t.knowledge_references,
                    "tool_calls": t.tool_calls,
                    "workflow_calls": t.workflow_calls,
                }

    return AgentRunDetail(
        id=run.id, status=run.status,
        created_at=run.created_at, completed_at=run.completed_at,
        conversation_id=run.conversation_id,
        steps=step_list, decision_trace=decision_trace,
    )
