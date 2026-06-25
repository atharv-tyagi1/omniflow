from uuid import UUID
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import time
import json

from backend.app.models.agent_telemetry import AgentDecisionTrace

class TelemetryEngine:
    """
    Captures metrics (latency, tokens, cost) and persists AgentDecisionTrace.
    Enforces strict privacy boundaries: stores only references, metadata, latency,
    tokens, cost, and tool/workflow calls.
    Explicitly redacts sensitive payloads and MUST NOT store raw secrets or 
    unrestricted hidden reasoning text.
    """

    _SENSITIVE_KEYS = {"password", "secret", "token", "key", "auth"}

    @classmethod
    def _redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redacts sensitive information from a dictionary."""
        redacted = {}
        for k, v in data.items():
            if any(s in k.lower() for s in cls._SENSITIVE_KEYS):
                redacted[k] = "[REDACTED]"
            elif isinstance(v, dict):
                redacted[k] = cls._redact_dict(v)
            elif isinstance(v, list):
                redacted[k] = [cls._redact_dict(i) if isinstance(i, dict) else i for i in v]
            else:
                redacted[k] = v
        return redacted

    @classmethod
    async def log_decision_trace(
        cls,
        db: AsyncSession,
        workspace_id: UUID,
        agent_id: UUID,
        run_id: UUID,
        step_id: UUID,
        provider: str,
        model: str,
        latency_ms: float,
        tokens_used: int,
        tools_called: List[Dict[str, Any]],
        context_metadata: Dict[str, Any],
        # We explicitly omit full prompts, reasoning, and raw completion from the signature
        # to guarantee they are not persisted here.
    ):
        """
        Persists a privacy-safe decision trace.
        """
        # Redact tool arguments if they contain secrets
        safe_tools = [cls._redact_dict(t) for t in tools_called]
        
        # Redact context metadata if it contains secrets
        safe_context = cls._redact_dict(context_metadata)

        trace = AgentDecisionTrace(
            workspace_id=workspace_id,
            agent_id=agent_id,
            agent_run_id=run_id,
            agent_run_step_id=step_id,
            trace_data={
                "provider": provider,
                "model": model,
                "latency_ms": latency_ms,
                "tokens_used": tokens_used,
                "tools_called": safe_tools,
                "context": safe_context
                # Intentionally omitting 'reasoning' or 'raw_prompt' 
                # to strictly abide by the privacy boundary constraint.
            }
        )
        db.add(trace)
        await db.commit()
