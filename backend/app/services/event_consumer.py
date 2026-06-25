"""Event Consumer for async workflow triggering."""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.workflow_event_queue import WorkflowEventQueue
from backend.app.models.workflow_run import WorkflowRun
from backend.app.services.workflow_service import WorkflowService
from backend.app.core.workflow.engine import WorkflowEngine


class EventConsumer:
    @staticmethod
    async def process_pending_events(db: AsyncSession):
        """Poll and process pending events."""
        stmt = select(WorkflowEventQueue).where(
            WorkflowEventQueue.status == "pending"
        ).order_by(WorkflowEventQueue.created_at.asc()).limit(10)
        
        result = await db.execute(stmt)
        events = result.scalars().all()
        
        for event in events:
            # Mark processing
            event.status = "processing"
            await db.commit()
            
            try:
                # Find matching workflows
                workflows = await WorkflowService.get_active_workflows_for_event(
                    db, event.workspace_id, event.event_type
                )
                
                engine = WorkflowEngine(db)
                
                for wf in workflows:
                    # Create run
                    run = WorkflowRun(
                        workflow_id=wf.id,
                        version_id=wf.active_version_id,
                        status="pending"
                    )
                    db.add(run)
                    await db.commit()
                    
                    # Execute async (fire and forget for now, though normally in a real task queue)
                    # For local asyncio, we can await it or spawn a task.
                    # Given FastAPI background tasks, this might be handled via celery/arq.
                    # We will await it directly for simplicity or spawn asyncio task.
                    asyncio.create_task(engine.execute_run(str(run.id), event.payload))
                    
                event.status = "processed"
            except Exception as e:
                event.status = "failed"
                event.error = str(e)
                # Retry logic
                if event.retry_count < 3:
                    event.retry_count += 1
                    event.status = "pending"
                else:
                    # Move to DLQ
                    from backend.app.models.workflow_dead_letter_event import WorkflowDeadLetterEvent
                    dlq = WorkflowDeadLetterEvent(
                        original_event_id=event.id,
                        workspace_id=event.workspace_id,
                        event_type=event.event_type,
                        payload=event.payload,
                        error_reason=str(e)
                    )
                    db.add(dlq)
            finally:
                await db.commit()
