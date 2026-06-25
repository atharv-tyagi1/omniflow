from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.workflow import Workflow
from backend.app.models.workflow_run import WorkflowRun
from backend.app.models.workflow_event_queue import WorkflowEventQueue
from backend.app.core.workflow.engine import WorkflowEngine
from sqlalchemy.future import select
from backend.app.repositories.workflow_repository import WorkflowRepository
from backend.app.core.exceptions import NotFoundError
from backend.app.services.outreach_service import OutreachService


class WorkflowService:
    @staticmethod
    async def create_workflow(
        db: AsyncSession, workspace_id: UUID, name: str, trigger_type: str
    ) -> Workflow:
        return await WorkflowRepository.create(
            db=db, workspace_id=workspace_id, name=name, trigger_type=trigger_type
        )

    @staticmethod
    async def get_workflow(
        db: AsyncSession, workflow_id: UUID, workspace_id: UUID
    ) -> Workflow:
        workflow = await WorkflowRepository.get_by_id(db, workflow_id, workspace_id)
        if not workflow:
            raise NotFoundError("Workflow not found")
        return workflow

    @staticmethod
    async def list_workflows(db: AsyncSession, workspace_id: UUID) -> List[Workflow]:
        return await WorkflowRepository.list_by_workspace(db, workspace_id)

    @staticmethod
    async def trigger_workflow(
        db: AsyncSession, workspace_id: UUID, workflow_id: UUID
    ) -> WorkflowRun:
        # Validate ownership
        await WorkflowService.get_workflow(db, workflow_id, workspace_id)

        run = await WorkflowRepository.create_run(
            db=db, workflow_id=workflow_id, status="running"
        )

        # Async execution of workflow actions would happen here
        # For proactive outreach workflows, we can trigger the evaluation manually here:
        try:
            await OutreachService.evaluate_triggers(db)
            execution_msg = (
                "Workflow executed and proactive outreach triggers evaluated."
            )
            status = "success"
        except Exception as e:
            execution_msg = f"Workflow execution failed: {str(e)}"
            status = "failed"

        run = await WorkflowRepository.update_run(
            db=db,
            run_id=run.id,
            status=status,
            execution_log={"steps": 1, "msg": execution_msg},
        )
        return run

    @staticmethod
    async def list_runs(db: AsyncSession, workspace_id: UUID, workflow_id: UUID) -> List[WorkflowRun]:
        # Validate ownership
        await WorkflowService.get_workflow(db, workflow_id, workspace_id)
        return await WorkflowRepository.list_runs_by_workflow(db, workflow_id)

    @staticmethod
    async def get_run_details(db: AsyncSession, workspace_id: UUID, workflow_id: UUID, run_id: UUID) -> WorkflowRun:
        # Validate ownership
        await WorkflowService.get_workflow(db, workflow_id, workspace_id)
        run = await WorkflowRepository.get_run_with_steps(db, run_id)
        if not run or run.workflow_id != workflow_id:
            raise NotFoundError("Run not found")
        return run

    @staticmethod
    async def dispatch_event(db: AsyncSession, workspace_id: UUID, event_type: str, payload: dict):
        """Queue an event for workflow processing."""
        event = WorkflowEventQueue(
            workspace_id=workspace_id,
            event_type=event_type,
            payload=payload,
            status="pending"
        )
        db.add(event)
        await db.commit()
        return event

    @staticmethod
    async def get_active_workflows_for_event(db: AsyncSession, workspace_id: UUID, event_type: str):
        """Find active workflows triggered by this event."""
        stmt = select(Workflow).where(
            Workflow.workspace_id == workspace_id,
            Workflow.trigger_type == event_type,
            Workflow.status == "active",
            Workflow.active_version_id.isnot(None)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
