from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Header, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging
from backend.app.core.database import get_db
from backend.app.core.public_auth import require_scope
from backend.app.core.rate_limiter import rate_limit
from backend.app.services.public.voice_service import PublicVoiceService
from backend.app.services.public.voice_providers import GeminiTranscriptionProvider, GTTSProvider
from backend.app.models.public_api import PublicAsyncJob
from backend.app.models.voice_interaction import VoiceInteraction
from backend.app.services.public.voice_storage import LocalVoiceStorage
from backend.app.core.telemetry import LatencyTracker, log_public_telemetry
import hashlib

router = APIRouter(prefix="/voice", tags=["public_voice"])
logger = logging.getLogger(__name__)

# Basic allowlist for demonstration
ALLOWED_MIME_TYPES = ["audio/wav", "audio/mpeg", "audio/ogg", "audio/mp4", "audio/x-m4a", "audio/webm"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("")
async def submit_voice_message(
    req: Request,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    external_customer_id: str = Form(...),
    customer_name: str = Form(...),
    customer_email: Optional[str] = Form(None),
    customer_phone: Optional[str] = Form(None),
    conversation_external_id: Optional[str] = Form(None),
    async_mode: bool = Form(False),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("chat")),
    _=Depends(rate_limit(limit=10, window_seconds=60))
):
    tracker = LatencyTracker()
    
    # 1. Auth and Scopes
    workspace_id = UUID(req.state.workspace_id)
    
    # 2. File Validation
    if audio.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    storage_service = LocalVoiceStorage()
    
    # 3. Stream Upload & Enforce Limits
    audio_ref, audio_hash, audio_size = await storage_service.stage_upload(audio)
    
    if audio_size > MAX_FILE_SIZE:
        await storage_service.delete_artifact(audio_ref)
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
    if audio_size == 0:
        await storage_service.delete_artifact(audio_ref)
        raise HTTPException(status_code=400, detail="Empty file")

    transcription_provider = GeminiTranscriptionProvider()
    tts_provider = GTTSProvider()

    if async_mode:
        # Create a pending VoiceInteraction so we don't put bytes in the job payload
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=30)
        
        voice_interaction = VoiceInteraction(
            workspace_id=workspace_id,
            idempotency_key=idempotency_key,
            channel="public_voice",
            input_audio_ref=audio_ref,
            input_audio_sha256=audio_hash,
            input_audio_mime_type=audio.content_type,
            input_audio_size_bytes=audio_size,
            artifact_created_at=now,
            artifact_expires_at=expires_at,
            status="pending"
        )
        db.add(voice_interaction)
        try:
            await db.flush()
        except Exception as e:
            await db.rollback()
            await storage_service.delete_artifact(audio_ref)
            
            # Idempotency hit: return existing
            from sqlalchemy import select
            stmt = select(VoiceInteraction).where(
                VoiceInteraction.workspace_id == workspace_id,
                VoiceInteraction.idempotency_key == idempotency_key
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=200, content={"status": "accepted", "duplicate": True, "voice_interaction_id": str(existing.id)})
            
            raise HTTPException(status_code=409, detail=f"Idempotency key {idempotency_key} already used but could not fetch existing record.")
            
        interaction_id = voice_interaction.id
        
        # Schedule the async job
        job = PublicAsyncJob(
            workspace_id=workspace_id,
            job_type="voice_message",
            result_payload={"voice_interaction_id": str(interaction_id)}
        )
        db.add(job)
        await db.commit()
        
        log_public_telemetry(
            "public_api_voice_async_submitted",
            workspace_id=str(workspace_id),
            details={"job_id": str(job.id), "interaction_id": str(interaction_id)},
            latency_ms=tracker.get_latency_ms()
        )
        
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=202, content={"job_id": str(job.id), "status": "accepted"})
        
    else:
        # Sync flow
        try:
            resp = await PublicVoiceService.run_voice_pipeline(
                db=db,
                workspace_id=workspace_id,
                idempotency_key=idempotency_key,
                audio_ref=audio_ref,
                audio_sha256=audio_hash,
                audio_size=audio_size,
                mime_type=audio.content_type,
                storage_service=storage_service,
                transcription_provider=transcription_provider,
                tts_provider=tts_provider,
                external_customer_id=external_customer_id,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                conversation_external_id=conversation_external_id
            )
            
            log_public_telemetry(
                "public_api_voice_sync_completed",
                workspace_id=str(workspace_id),
                details={"interaction_id": resp.get("voice_interaction_id")},
                latency_ms=tracker.get_latency_ms()
            )
            
            return resp
        except ValueError as ve:
            raise HTTPException(status_code=409, detail=str(ve))
        except Exception as e:
            logger.error(f"Sync voice request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal server error processing voice message")
