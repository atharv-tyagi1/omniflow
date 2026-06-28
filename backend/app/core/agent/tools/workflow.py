"""Workflow Tool — triggers Phase 21.1 WorkflowService from the Agent Runtime."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


async def trigger_workflow(
    workflow_id: str,
    workspace_id: str,
    payload: Optional[Dict[str, Any]] = None,
    db: Any = None,  # AsyncSession passed at call time
) -> Dict[str, Any]:
    """
    Invokes WorkflowService.trigger_workflow, reusing the Phase 21.1 Engine.
    Strictly validates workspace ownership before execution (no cross-tenant calls).
    """
    if not workflow_id or not workspace_id:
        return {"status": "error", "message": "workflow_id and workspace_id are required"}

    if db is None:
        logger.warning("No DB session provided to workflow tool — using database session pool")
        from backend.app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            return await _execute_workflow(session, workflow_id, workspace_id, payload or {})

    return await _execute_workflow(db, workflow_id, workspace_id, payload or {})


async def _execute_workflow(
    db: Any,
    workflow_id: str,
    workspace_id: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    try:
        from backend.app.services.workflow_service import WorkflowService

        run = await WorkflowService.trigger_workflow(
            db=db,
            workspace_id=UUID(workspace_id),
            workflow_id=UUID(workflow_id),
        )
        logger.info(
            f"Workflow {workflow_id} triggered by agent runtime — "
            f"run_id={run.id} status={run.status}"
        )
        return {
            "status": run.status,
            "run_id": str(run.id),
            "workflow_id": workflow_id,
            "message": f"Workflow executed with status: {run.status}",
        }
    except Exception as e:
        logger.error(f"Workflow {workflow_id} execution failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "workflow_id": workflow_id,
        }
