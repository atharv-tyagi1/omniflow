import uuid
from typing import Any
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.public_auth import require_scope
from backend.app.core.rate_limiter import rate_limit
from backend.app.core.public_errors import PublicAPIException
from backend.app.schemas.public_api import (
    PublicResponse,
    PublicChatRequest,
    PublicChatResponse,
    PublicAsyncJobResponse,
    PublicAsyncJobStatus
)
from backend.app.models.public_api import PublicAsyncJob
from backend.app.services.public.idempotency_service import IdempotencyService
from backend.app.services.public.chat_service import PublicChatService

router = APIRouter(prefix="/chat", tags=["public_chat"])

@router.post("", response_model=PublicResponse[Any])
async def submit_chat(
    req: Request,
    payload: PublicChatRequest,
    idempotency_key: str = Header(..., description="Idempotency key for safe retries"),
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("chat")),
    _=Depends(rate_limit(limit=10, window_seconds=60))
):
    workspace_id = uuid.UUID(req.state.workspace_id)
    
    # Check Idempotency
    record, is_new = await IdempotencyService.get_or_create_idempotency_key(
        db, workspace_id, idempotency_key, req.url.path
    )
    if not is_new:
        if record.status == "completed":
            return PublicResponse(success=True, data=record.response_body)
        elif record.status == "failed":
            raise PublicAPIException("Previous request failed. Please use a new idempotency key.", status_code=400, code="PREVIOUS_REQUEST_FAILED")

    try:
        if payload.response_mode == "async":
            from datetime import datetime, timezone, timedelta
            from backend.app.core.config import settings
            
            # Create durable async job (to be polled by PublicAsyncJobWorker)
            retention_days = getattr(settings, "ASYNC_JOB_RETENTION_DAYS", 30)
            expires_at = datetime.now(timezone.utc) + timedelta(days=retention_days)
            
            job = PublicAsyncJob(
                workspace_id=workspace_id,
                job_type="chat_message",
                status="pending",
                expires_at=expires_at,
                result_payload=payload.model_dump() # Store the request payload for the worker to execute
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            
            response_data = PublicAsyncJobResponse(
                job_id=str(job.id),
                status_url=f"/api/public/v1/chat/jobs/{job.id}"
            ).model_dump()
            
            await IdempotencyService.complete_idempotency_request(db, record, response_data)
            from fastapi.responses import JSONResponse
            content = PublicResponse(success=True, data=response_data).model_dump()
            return JSONResponse(status_code=202, content=content)
        
        else:
            # Sync mode
            chat_resp = await PublicChatService.process_sync_chat(
                db=db,
                workspace_id=workspace_id,
                external_customer_id=payload.external_customer_id,
                customer_name=payload.customer_name,
                message=payload.message,
                customer_email=payload.customer_email,
                customer_phone=payload.customer_phone,
                conversation_external_id=payload.conversation_external_id
            )
            await IdempotencyService.complete_idempotency_request(db, record, chat_resp)
            return PublicResponse(success=True, data=chat_resp)
            
    except Exception as e:
        await IdempotencyService.fail_idempotency_request(db, record)
        raise e


@router.get("/jobs/{job_id}", response_model=PublicResponse[PublicAsyncJobStatus])
async def get_chat_job_status(
    req: Request,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("chat")),
    _=Depends(rate_limit(limit=60, window_seconds=60))
):
    workspace_id = uuid.UUID(req.state.workspace_id)
    stmt = select(PublicAsyncJob).where(
        PublicAsyncJob.workspace_id == workspace_id,
        PublicAsyncJob.id == job_id
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise PublicAPIException("Job not found", status_code=404, code="JOB_NOT_FOUND")

    data = PublicAsyncJobStatus(
        job_id=str(job.id),
        status=job.status,
        result=job.result_payload,
        error=job.last_error or job.error_message
    )
    return PublicResponse(success=True, data=data)
