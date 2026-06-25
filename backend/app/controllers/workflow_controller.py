from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.workflow_service import WorkflowService
from backend.app.models.workflow_run import WorkflowRun
from backend.app.models.workflow import Workflow
from backend.app.services.workflow_builder_service import WorkflowBuilderService
from backend.app.schemas.workflow_builder import WorkflowDraftUpdate


class WorkflowController:
    @staticmethod
    async def create(
        db: AsyncSession, workspace_id: UUID, name: str, trigger_type: str
    ) -> Workflow:
        return await WorkflowService.create_workflow(
            db=db, workspace_id=workspace_id, name=name, trigger_type=trigger_type
        )

    @staticmethod
    async def get_all(db: AsyncSession, workspace_id: UUID) -> List[Workflow]:
        return await WorkflowService.list_workflows(db, workspace_id)

    @staticmethod
    async def get_by_id(
        db: AsyncSession, workflow_id: UUID, workspace_id: UUID
    ) -> Workflow:
        return await WorkflowService.get_workflow(db, workflow_id, workspace_id)

    @staticmethod
    async def trigger(
        db: AsyncSession, workspace_id: UUID, workflow_id: UUID
    ) -> WorkflowRun:
        return await WorkflowService.trigger_workflow(
            db=db, workspace_id=workspace_id, workflow_id=workflow_id
        )

    @staticmethod
    async def get_workflow_draft(db: AsyncSession, workspace_id: UUID, workflow_id: UUID):
        return await WorkflowBuilderService.get_workflow_draft(db, workspace_id, workflow_id)

    @staticmethod
    async def list_runs(db: AsyncSession, workspace_id: UUID, workflow_id: UUID):
        return await WorkflowService.list_runs(db, workspace_id, workflow_id)

    @staticmethod
    async def get_run_details(db: AsyncSession, workspace_id: UUID, workflow_id: UUID, run_id: UUID):
        return await WorkflowService.get_run_details(db, workspace_id, workflow_id, run_id)

    @staticmethod
    async def save_draft(db: AsyncSession, workspace_id: UUID, workflow_id: UUID, draft: WorkflowDraftUpdate):
        return await WorkflowBuilderService.save_draft(db, workspace_id, workflow_id, draft)

    @staticmethod
    async def publish(db: AsyncSession, workspace_id: UUID, workflow_id: UUID):
        return await WorkflowBuilderService.publish(db, workspace_id, workflow_id)
