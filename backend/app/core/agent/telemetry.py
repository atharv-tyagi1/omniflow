"""Telemetry Engine — writes AgentRun, AgentRunStep, AgentDecisionTrace, and AgentLog to DB."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.agent_run import AgentRun
from backend.app.models.agent_run_step import AgentRunStep
from backend.app.models.agent_decision_trace import AgentDecisionTrace
from backend.app.models.agent_log import AgentLog
from backend.app.models.agent_metric import AgentMetric

logger = logging.getLogger(__name__)

# Sensitive keys to redact from telemetry payloads
_REDACTED_KEYS = {"api_key", "password", "secret", "token", "authorization", "bearer", "raw_reasoning", "hidden_reasoning", "reasoning_text"}


def _redact(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redacts known sensitive keys from a dict."""
    if not isinstance(data, dict):
        return data
    result: Dict[str, Any] = {}
    for k, v in data.items():
        if k.lower() in _REDACTED_KEYS:
            result[k] = "***REDACTED***"
        elif isinstance(v, dict):
            result[k] = _redact(v)
        else:
            result[k] = v
    return result


class TelemetryEngine:
    """
    Captures and persists all runtime observability:
    - AgentRun lifecycle (created → completed/failed)
    - AgentRunStep per execution step
    - AgentDecisionTrace with full audit trail
    - AgentLog structured entries
    - AgentMetric aggregation hooks

    Enforces: no raw secrets, no leaked reasoning text stored as-is.
    """

    # ──────────────────────────────────────────────────────────────────────────
    # RUN LIFECYCLE
    # ──────────────────────────────────────────────────────────────────────────

    async def create_run(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        agent_id: UUID,
        version_id: UUID,
        conversation_id: UUID,
    ) -> AgentRun:
        """Creates an AgentRun record at the start of execution."""
        run = AgentRun(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            agent_id=agent_id,
            version_id=version_id,
            conversation_id=conversation_id,
            status="running",
        )
        db.add(run)
        await db.flush()
        logger.info(
            f"AgentRun created: run_id={run.id} agent={agent_id} "
            f"workspace={workspace_id} conversation={conversation_id}"
        )
        return run

    async def complete_run(
        self,
        db: AsyncSession,
        run: AgentRun,
        status: str = "success",
    ) -> None:
        """Marks an AgentRun as completed."""
        run.status = status
        run.completed_at = datetime.now(timezone.utc)
        db.add(run)
        await db.flush()
        logger.info(f"AgentRun {run.id} completed with status={status}")

    # ──────────────────────────────────────────────────────────────────────────
    # RUN STEPS
    # ──────────────────────────────────────────────────────────────────────────

    async def record_step(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        run_id: UUID,
        step_type: str,
        payload: Optional[Dict[str, Any]],
        latency_ms: int,
    ) -> AgentRunStep:
        """Records an individual execution step (llm_call, tool_execution, rag_retrieval)."""
        safe_payload = _redact(payload or {})
        step = AgentRunStep(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            run_id=run_id,
            step_type=step_type,
            payload=safe_payload,
            latency_ms=latency_ms,
        )
        db.add(step)
        await db.flush()
        logger.debug(f"AgentRunStep recorded: type={step_type} run={run_id} latency={latency_ms}ms")
        return step

    # ──────────────────────────────────────────────────────────────────────────
    # DECISION TRACE
    # ──────────────────────────────────────────────────────────────────────────

    async def persist_decision_trace(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        run_step: AgentRunStep,
        prompt_version_id: Optional[UUID],
        memory_references: List[str],
        knowledge_references: List[str],
        tool_calls: List[Dict[str, Any]],
        workflow_calls: List[Dict[str, Any]],
        model_used: str,
        latency_ms: int,
        cost_tokens: int,
        execution_metadata: Dict[str, Any],
    ) -> AgentDecisionTrace:
        """Persists the full decision trace for an execution step."""
        trace = AgentDecisionTrace(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            run_step_id=run_step.id,
            prompt_version_id=prompt_version_id,
            memory_references=memory_references,
            knowledge_references=knowledge_references,
            tool_calls=_redact({"calls": tool_calls}).get("calls", []),
            workflow_calls=_redact({"calls": workflow_calls}).get("calls", []),
            model_used=model_used,
            latency_ms=latency_ms,
            cost_tokens=cost_tokens,
            execution_metadata=_redact(execution_metadata),
        )
        db.add(trace)
        await db.flush()
        logger.debug(
            f"AgentDecisionTrace persisted: step={run_step.id} "
            f"model={model_used} tokens={cost_tokens} latency={latency_ms}ms"
        )
        return trace

    # ──────────────────────────────────────────────────────────────────────────
    # STRUCTURED LOGS
    # ──────────────────────────────────────────────────────────────────────────

    async def log(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        agent_id: UUID,
        run_id: Optional[UUID],
        level: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Writes a structured log entry to agent_logs."""
        try:
            entry = AgentLog(
                id=uuid.uuid4(),
                workspace_id=workspace_id,
                agent_id=agent_id,
                run_id=run_id,
                level=level,
                message=message,
                details=_redact(details or {}),
            )
            db.add(entry)
            await db.flush()
        except Exception as e:
            # Never crash the runtime because of a logging failure
            logger.error(f"Failed to write AgentLog: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # ANALYTICS HOOKS
    # ──────────────────────────────────────────────────────────────────────────

    async def increment_metric(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        agent_id: UUID,
        tokens: int,
        cost: float,
    ) -> None:
        """
        Updates (or creates) the daily AgentMetric aggregation row.
        This is a lightweight hook — full aggregation pipeline is Phase 21.4.
        """
        try:
            from sqlalchemy import select, func
            today = datetime.now(timezone.utc).date()

            result = await db.execute(
                select(AgentMetric).where(
                    AgentMetric.workspace_id == workspace_id,
                    AgentMetric.agent_id == agent_id,
                    AgentMetric.metric_date == today,
                )
            )
            metric = result.scalars().first()

            if metric:
                metric.total_tokens = (metric.total_tokens or 0) + tokens
                metric.total_cost = (metric.total_cost or 0.0) + cost
                metric.total_conversations = (metric.total_conversations or 0) + 1
            else:
                metric = AgentMetric(
                    id=uuid.uuid4(),
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    metric_date=today,
                    total_tokens=tokens,
                    total_cost=cost,
                    total_conversations=1,
                )
                db.add(metric)

            await db.flush()
        except Exception as e:
            logger.warning(f"Failed to increment AgentMetric: {e}")
