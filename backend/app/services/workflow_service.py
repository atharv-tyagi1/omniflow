from uuid import UUID
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.workflow import Workflow
from backend.app.models.workflow_run import WorkflowRun
from backend.app.repositories.workflow_repository import WorkflowRepository
from backend.app.core.exceptions import NotFoundError
from backend.app.services.outreach_service import OutreachService

class WorkflowService:
    @staticmethod
    async def create_workflow(
        db: AsyncSession,
        workspace_id: UUID,
        name: str,
        trigger_type: str
    ) -> Workflow:
        return await WorkflowRepository.create(
            db=db,
            workspace_id=workspace_id,
            name=name,
            trigger_type=trigger_type
        )

    @staticmethod
    async def get_workflow(db: AsyncSession, workflow_id: UUID, workspace_id: UUID) -> Workflow:
        workflow = await WorkflowRepository.get_by_id(db, workflow_id, workspace_id)
        if not workflow:
            raise NotFoundError("Workflow not found")
        return workflow

    @staticmethod
    async def list_workflows(db: AsyncSession, workspace_id: UUID) -> List[Workflow]:
        return await WorkflowRepository.list_by_workspace(db, workspace_id)

    @staticmethod
    async def trigger_workflow(
        db: AsyncSession,
        workspace_id: UUID,
        workflow_id: UUID
    ) -> WorkflowRun:
        # Validate ownership
        await WorkflowService.get_workflow(db, workflow_id, workspace_id)

        run = await WorkflowRepository.create_run(
            db=db,
            workflow_id=workflow_id,
            status="running"
        )
        
        # Async execution of workflow actions would happen here
        # For proactive outreach workflows, we can trigger the evaluation manually here:
        try:
            await OutreachService.evaluate_triggers(db)
            execution_msg = "Workflow executed and proactive outreach triggers evaluated."
            status = "success"
        except Exception as e:
            execution_msg = f"Workflow execution failed: {str(e)}"
            status = "failed"
        
        # For now, immediately complete it
        run = await WorkflowRepository.update_run(
            db=db,
            run_id=run.id,
            status=status,
            execution_log={"steps": 1, "msg": execution_msg}
        )
        return run
