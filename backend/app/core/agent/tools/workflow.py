from uuid import UUID
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.workflow_service import WorkflowService
from backend.app.core.agent.tool_engine import ToolEngine

async def trigger_workflow_tool(
    db: AsyncSession,
    workspace_id: UUID,
    workflow_id: UUID,
    inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Tool implementation that invokes WorkflowService.trigger_workflow.
    
    Execution is strictly asynchronous and non-blocking: the runtime must suspend,
    yield control, and resume upon callback or completion signal rather than 
    blocking the event loop. In this implementation, trigger_workflow returns
    the state or a job ID immediately (asynchronous invocation).
    """
    return await WorkflowService.trigger_workflow(
        db=db,
        workflow_id=workflow_id,
        initial_state=inputs
    )

# Register it with the ToolEngine
ToolEngine.register_tool("trigger_workflow", trigger_workflow_tool)
