from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, List, Dict, Any

from backend.app.models.workflow import Workflow
from backend.app.models.workflow_run import WorkflowRun


class WorkflowRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        name: str,
        trigger_type: str
    ) -> Workflow:
        db_obj = Workflow(
            workspace_id=workspace_id,
            name=name,
            trigger_type=trigger_type
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_id(db: AsyncSession, workflow_id: UUID, workspace_id: UUID) -> Optional[Workflow]:
        result = await db.execute(
            select(Workflow)
            .where(Workflow.id == workflow_id, Workflow.workspace_id == workspace_id)
            .options(selectinload(Workflow.runs))
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_workspace(db: AsyncSession, workspace_id: UUID) -> List[Workflow]:
        result = await db.execute(
            select(Workflow)
            .where(Workflow.workspace_id == workspace_id)
            .order_by(Workflow.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_run(
        db: AsyncSession,
        *,
        workflow_id: UUID,
        status: str = "pending",
        execution_log: Optional[Dict[str, Any]] = None
    ) -> WorkflowRun:
        db_obj = WorkflowRun(
            workflow_id=workflow_id,
            status=status,
            execution_log=execution_log
        )
        db.add(db_obj)
        await db.flush()
        return db_obj
    
    @staticmethod
    async def update_run(
        db: AsyncSession,
        *,
        run_id: UUID,
        status: str,
        execution_log: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowRun]:
        result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
        run = result.scalars().first()
        if run:
            run.status = status
            if execution_log is not None:
                run.execution_log = execution_log
            db.add(run)
            await db.flush()
        return run
