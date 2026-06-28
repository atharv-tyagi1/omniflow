"""
Phase 21.2F — Public Agent Chat API
Exposes: POST /api/public/v1/agents/{agent_id}/chat
         POST /api/public/v1/agents/{agent_id}/chat/stream

Security: X-Api-Key via `require_scope("agent_chat")`.
Shared controls: rate limiting, audit logging, idempotency — all preserved.
Only agents with `is_public_allowed=True` are served.
"""
import uuid
import asyncio
import json
import logging
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.public_auth import require_scope
from backend.app.core.rate_limiter import rate_limit
from backend.app.core.public_errors import PublicAPIException
from backend.app.schemas.public_api import PublicResponse
from backend.app.schemas.agent_builder import AgentChatRequest
from backend.app.models.agent import Agent
from backend.app.services.agent_service import AgentService
from backend.app.services.public.idempotency_service import IdempotencyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["public_agents"])


async def _resolve_public_agent(
    db: AsyncSession,
    agent_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> Agent:
    """
    Load the agent, enforcing:
    - Workspace ownership
    - is_public_allowed=True
    - is_active=True
    """
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.workspace_id == workspace_id,
            Agent.is_active == True,
        )
    )
    agent = result.scalars().first()
    if not agent:
        raise PublicAPIException("Agent not found", status_code=404, code="NOT_FOUND")
    if not getattr(agent, "is_public_allowed", False):
        raise PublicAPIException(
            "This agent is not available on the public API",
            status_code=403,
            code="FORBIDDEN",
        )
    return agent


@router.post("/{agent_id}/chat", response_model=PublicResponse[Any])
async def public_chat(
    req: Request,
    agent_id: uuid.UUID,
    payload: AgentChatRequest,
    idempotency_key: str = Header(..., description="Idempotency key for safe retries"),
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("agent_chat")),
    _=Depends(rate_limit(limit=20, window_seconds=60)),
):
    """
    Public chat endpoint. Only serves public-allowed agents.
    X-Api-Key required with scope 'agent_chat'.
    """
    workspace_id = uuid.UUID(req.state.workspace_id)

    # Idempotency check
    record, is_new = await IdempotencyService.get_or_create_idempotency_key(
        db, workspace_id, idempotency_key, req.url.path
    )
    if not is_new:
        if record.status == "completed":
            return PublicResponse(success=True, data=record.response_body)
        elif record.status == "failed":
            raise PublicAPIException(
                "Previous request failed. Use a new idempotency key.",
                status_code=400,
                code="PREVIOUS_REQUEST_FAILED",
            )

    try:
        # Validate public access
        await _resolve_public_agent(db, agent_id, workspace_id)

        conversation_id = payload.conversation_id or uuid.uuid4()
        result = await AgentService.dispatch(
            db=db,
            workspace_id=workspace_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            user_message=payload.message,
        )

        response_data = {
            "content": result.get("content", ""),
            "status": result.get("status", "success"),
            "conversation_id": str(conversation_id),
            "run_id": result.get("run_id"),
            "latency_ms": result.get("latency_ms", 0),
            "tokens_used": result.get("tokens_used", 0),
        }
        await IdempotencyService.complete_idempotency_request(db, record, response_data)
        return PublicResponse(success=True, data=response_data)

    except PublicAPIException:
        await IdempotencyService.fail_idempotency_request(db, record)
        raise
    except Exception as e:
        await IdempotencyService.fail_idempotency_request(db, record)
        logger.error(f"Public agent chat error agent={agent_id}: {e}", exc_info=True)
        raise PublicAPIException("Agent execution failed", status_code=500, code="INTERNAL_ERROR")


@router.post("/{agent_id}/chat/stream")
async def public_chat_stream(
    req: Request,
    agent_id: uuid.UUID,
    payload: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("agent_chat")),
    _=Depends(rate_limit(limit=10, window_seconds=60)),
):
    """
    SSE streaming public chat. Implements:
    - Cancellation on client disconnect
    - Heartbeat/keepalive every 10s
    - Backpressure-safe event emission
    """
    workspace_id = uuid.UUID(req.state.workspace_id)

    # Validate public access before streaming begins
    await _resolve_public_agent(db, agent_id, workspace_id)
    conversation_id = payload.conversation_id or uuid.uuid4()

    async def sse_generator() -> AsyncGenerator[str, None]:
        try:
            yield f"event: start\ndata: {json.dumps({'conversation_id': str(conversation_id)})}\n\n"

            task = asyncio.create_task(
                AgentService.dispatch(
                    db=db,
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    conversation_id=conversation_id,
                    user_message=payload.message,
                )
            )

            # Poll with heartbeat while agent runs
            while not task.done():
                if await req.is_disconnected():
                    task.cancel()
                    logger.info(f"Public SSE client disconnected: agent={agent_id}")
                    return
                yield f"event: heartbeat\ndata: {{}}\n\n"
                await asyncio.sleep(5)

            result = await task
            yield f"event: chunk\ndata: {json.dumps({'content': result.get('content', '')})}\n\n"
            yield (
                f"event: done\ndata: "
                f"{json.dumps({'status': result.get('status','success'), 'tokens_used': result.get('tokens_used', 0)})}\n\n"
            )

        except asyncio.CancelledError:
            yield f"event: cancelled\ndata: {json.dumps({'reason': 'client_disconnect'})}\n\n"
        except Exception as e:
            logger.error(f"Public SSE error agent={agent_id}: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': 'Agent execution failed'})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
