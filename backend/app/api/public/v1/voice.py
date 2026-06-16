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
        
    audio_bytes = await audio.read()
    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    transcription_provider = GeminiTranscriptionProvider()
    tts_provider = GTTSProvider()

    if async_mode:
        # Create a pending VoiceInteraction so we don't put bytes in the job payload
        audio_size = len(audio_bytes)
        audio_hash = hashlib.sha256(audio_bytes).hexdigest()
        
        voice_interaction = VoiceInteraction(
            workspace_id=workspace_id,
            idempotency_key=idempotency_key,
            channel="public_voice",
            input_audio_sha256=audio_hash,
            input_audio_mime_type=audio.content_type,
            input_audio_size_bytes=audio_size,
            input_audio_bytes=audio_bytes,
            status="pending"
        )
        db.add(voice_interaction)
        try:
            await db.flush()
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=409, detail=f"Idempotency key {idempotency_key} already used.")
            
        interaction_id = voice_interaction.id
        
        # Schedule the async job
        job = PublicAsyncJob(
            workspace_id=workspace_id,
            idempotency_key=f"job_voice_{idempotency_key}",
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
                audio_bytes=audio_bytes,
                mime_type=audio.content_type,
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
