import logging
import asyncio
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_, or_

from backend.app.models.public_api import PublicAsyncJob
from backend.app.services.public.chat_service import PublicChatService
from backend.app.core.telemetry import log_public_telemetry, LatencyTracker
from backend.app.core.public_errors import PublicAPIException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class PublicAsyncJobWorker:
    """
    Worker for processing Public API async jobs durably and atomically.
    """
    
    @staticmethod
    def _is_transient_error(e: Exception) -> bool:
        """
        Classifier to determine if an error is transient (retryable) or permanent.
        """
        if isinstance(e, PublicAPIException):
            # Example: Rate limits or upstream timeouts are transient
            if e.status_code in (429, 502, 503, 504):
                return True
            return False
            
        if isinstance(e, RequestValidationError):
            return False
            
        if isinstance(e, IntegrityError):
            return False
            
        # Treat unknown exceptions as transient by default but we could also treat as permanent.
        # Let's treat standard DB/network connection errors as transient if we could distinguish them.
        # For safety, let's treat generic Exceptions as transient to allow retry on generic failures.
        return True

    @staticmethod
    async def process_pending_jobs(db: AsyncSession, batch_size: int = 10):
        """
        Polls for pending (or retryable failed) jobs, claims them atomically, and processes them.
        """
        # Atomically claim jobs
        # In PostgreSQL we can do UPDATE ... RETURNING to claim safely.
        # Find jobs that are pending, or failed but with attempts < max_attempts
        
        # We need raw SQL or a specific ORM construct for UPDATE RETURNING
        # Since SQLAlchemy `update` doesn't natively support SKIP LOCKED inside the UPDATE cleanly without subqueries,
        # we can use a CTE or just select with for_update(skip_locked=True)
        
        stmt = select(PublicAsyncJob).where(
            or_(
                PublicAsyncJob.status == "pending",
                and_(
                    PublicAsyncJob.status == "failed",
                    PublicAsyncJob.attempts < PublicAsyncJob.max_attempts
                )
            )
        ).limit(batch_size).with_for_update(skip_locked=True)
        
        result = await db.execute(stmt)
        jobs_to_process = result.scalars().all()
        print("JOBS TO PROCESS COUNT:", len(jobs_to_process))
        for j in jobs_to_process:
            print(f"JOB: id={j.id}, type={j.job_type}, status={j.status}")
        
        if not jobs_to_process:
            return
            
        for job in jobs_to_process:
            # Mark processing
            job.status = "processing"
            job.attempts += 1
        
        await db.commit()
        
        # Process claimed jobs
        for job in jobs_to_process:
            tracker = LatencyTracker()
            job_id = job.id
            try:
                if job.job_type == "chat_message":
                    payload = job.result_payload or {}
                    
                    chat_resp = await PublicChatService.process_sync_chat(
                        db=db,
                        workspace_id=job.workspace_id,
                        external_customer_id=payload.get("external_customer_id"),
                        customer_name=payload.get("customer_name"),
                        message=payload.get("message"),
                        customer_email=payload.get("customer_email"),
                        customer_phone=payload.get("customer_phone"),
                        conversation_external_id=payload.get("conversation_external_id")
                    )
                    
                    job.status = "completed"
                    job.result_payload = chat_resp
                    job.last_error = None
                    
                    log_public_telemetry(
                        "public_async_job_completed",
                        workspace_id=str(job.workspace_id),
                        details={"job_id": str(job_id), "job_type": job.job_type, "attempts": job.attempts},
                        latency_ms=tracker.get_latency_ms()
                    )
                elif job.job_type == "telegram_update":
                    payload = job.result_payload or {}
                    from backend.app.services.telegram_service import TelegramService
                    
                    await TelegramService.process_update(db=db, update=payload)
                    
                    job.status = "completed"
                    job.result_payload = {"status": "success"}
                    job.last_error = None
                    
                    log_public_telemetry(
                        "public_async_job_completed",
                        workspace_id=str(job.workspace_id),
                        details={"job_id": str(job_id), "job_type": job.job_type, "attempts": job.attempts},
                        latency_ms=tracker.get_latency_ms()
                    )
                elif job.job_type == "voice_message":
                    payload = job.result_payload or {}
                    from backend.app.services.public.voice_service import PublicVoiceService
                    
                    voice_resp = await PublicVoiceService.process_async_voice_job(
                        db=db,
                        workspace_id=job.workspace_id,
                        payload=payload
                    )
                    
                    job.status = "completed"
                    job.result_payload = voice_resp
                    job.last_error = None
                    
                    log_public_telemetry(
                        "public_async_job_completed",
                        workspace_id=str(job.workspace_id),
                        details={"job_id": str(job_id), "job_type": job.job_type, "attempts": job.attempts},
                        latency_ms=tracker.get_latency_ms()
                    )
                else:
                    raise ValueError(f"Unknown job_type: {job.job_type}")
                    
                await db.commit()
                
            except Exception as e:
                print("ASYNC JOB WORKER EXCEPTION:", str(e))
                import traceback
                traceback.print_exc()
                await db.rollback()
                
                # Re-fetch to update status
                result = await db.execute(select(PublicAsyncJob).where(PublicAsyncJob.id == job_id))
                fresh_job = result.scalar_one()
                
                error_msg = str(e)
                fresh_job.last_error = error_msg
                
                if PublicAsyncJobWorker._is_transient_error(e) and fresh_job.attempts < fresh_job.max_attempts:
                    fresh_job.status = "pending" # will be picked up again
                    log_public_telemetry(
                        "public_async_job_retrying",
                        workspace_id=str(fresh_job.workspace_id),
                        details={"job_id": str(fresh_job.id), "error": error_msg, "attempts": fresh_job.attempts},
                        latency_ms=tracker.get_latency_ms()
                    )
                else:
                    fresh_job.status = "failed"
                    log_public_telemetry(
                        "public_async_job_failed",
                        workspace_id=str(fresh_job.workspace_id),
                        details={"job_id": str(fresh_job.id), "error": error_msg, "permanent": True},
                        latency_ms=tracker.get_latency_ms()
                    )
                    
                await db.commit()
