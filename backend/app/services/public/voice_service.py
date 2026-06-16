import hashlib
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.services.conversation_service import ConversationService
from backend.app.models.voice_interaction import VoiceInteraction
from backend.app.services.public.voice_providers import BaseTranscriptionProvider, BaseTTSProvider, GeminiTranscriptionProvider, GTTSProvider

logger = logging.getLogger(__name__)

class PublicVoiceService:
    @staticmethod
    async def run_voice_pipeline(
        db: AsyncSession,
        workspace_id: UUID,
        idempotency_key: str,
        audio_bytes: bytes,
        mime_type: str,
        transcription_provider: BaseTranscriptionProvider,
        tts_provider: BaseTTSProvider,
        external_customer_id: str,
        customer_name: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        conversation_external_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        
        # 1. Upsert customer
        customer = await CustomerRepository.upsert_by_external_id(
            db=db,
            workspace_id=workspace_id,
            external_id=external_customer_id,
            name=customer_name,
            email=customer_email,
            phone=customer_phone
        )

        # 2. Resolve or create active conversation
        conversation = await ConversationService.get_active_by_customer(
            db=db, customer_id=customer.id, channel="public_voice"
        )
        if not conversation:
            conversation = await ConversationService.create_conversation(
                db=db,
                workspace_id=workspace_id,
                customer_id=customer.id,
                channel="public_voice"
            )
            if conversation_external_id:
                conversation.external_id = conversation_external_id
                await db.commit()

        # 3 & 4. Validate voice request idempotency and Create VoiceInteraction
        audio_size = len(audio_bytes)
        audio_hash = hashlib.sha256(audio_bytes).hexdigest()

        voice_interaction = VoiceInteraction(
            workspace_id=workspace_id,
            customer_id=customer.id,
            conversation_id=conversation.id,
            idempotency_key=idempotency_key,
            channel="public_voice",
            input_audio_sha256=audio_hash,
            input_audio_mime_type=mime_type,
            input_audio_size_bytes=audio_size,
            input_audio_bytes=audio_bytes,
            status="processing"
        )
        db.add(voice_interaction)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise ValueError(f"Idempotency key {idempotency_key} already used.")

        try:
            # 5. Transcribe audio
            transcript = await transcription_provider.transcribe(audio_bytes, mime_type)
            voice_interaction.transcript_text = transcript
            await db.flush()

            # 6. Dispatch transcript to ConversationService
            result = await ConversationService.add_message(
                db=db,
                conversation_id=conversation.id,
                workspace_id=workspace_id,
                sender_type="customer",
                content=transcript
            )

            # 7 & 8. Save reply text
            if result.agent_message:
                reply_text = result.agent_message.content
                voice_interaction.reply_text = reply_text
                await db.flush()

                # 9. Run TTS generation
                try:
                    reply_audio_bytes = await tts_provider.synthesize(reply_text)
                    voice_interaction.reply_audio_bytes = reply_audio_bytes
                    voice_interaction.status = "completed"
                except Exception as tts_err:
                    logger.error(f"TTS generation failed: {tts_err}")
                    voice_interaction.error_code = "TTS_FAILED"
                    voice_interaction.error_message = str(tts_err)
                    voice_interaction.status = "completed_with_errors"
            else:
                voice_interaction.status = "completed"

            await db.commit()
            
            # 10. Return dict matching PublicVoiceResponse
            return {
                "idempotency_key": idempotency_key,
                "voice_interaction_id": str(voice_interaction.id),
                "conversation_id": str(conversation.id),
                "customer_message_id": str(result.customer_message.id),
                "agent_message_id": str(result.agent_message.id) if result.agent_message else None,
                "transcript": voice_interaction.transcript_text,
                "reply_text": voice_interaction.reply_text,
                "status": voice_interaction.status,
                "has_audio_reply": voice_interaction.reply_audio_bytes is not None
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Voice pipeline failed: {e}")
            
            # Record failure in the interaction record
            voice_interaction.status = "failed"
            voice_interaction.error_message = str(e)
            db.add(voice_interaction)
            await db.commit()
            
            raise

    @staticmethod
    async def process_async_voice_job(
        db: AsyncSession,
        workspace_id: UUID,
        payload: dict
    ) -> dict:
        """
        Invoked by the async worker. The payload will contain the DB reference
        or the bytes if we passed them via kwargs (though we shouldn't pass bytes in payload).
        Wait, for async job, we don't put bytes in payload. We just fetch the VoiceInteraction record
        which has the bytes, or we pass the VoiceInteraction ID.
        """
        interaction_id = payload.get("voice_interaction_id")
        if not interaction_id:
            raise ValueError("voice_interaction_id missing from payload")
            
        voice_interaction = await db.get(VoiceInteraction, UUID(interaction_id))
        if not voice_interaction:
            raise ValueError(f"VoiceInteraction {interaction_id} not found")
            
        transcription_provider = GeminiTranscriptionProvider()
        tts_provider = GTTSProvider()

        # The pipeline logic is slightly different here because the interaction is already created.
        # But we can extract the pipeline logic into a shared helper if needed, or implement the rest here.
        # Let's run the steps 5-10
        audio_bytes = voice_interaction.input_audio_bytes
        mime_type = voice_interaction.input_audio_mime_type
        
        try:
            transcript = await transcription_provider.transcribe(audio_bytes, mime_type)
            voice_interaction.transcript_text = transcript
            await db.flush()

            result = await ConversationService.add_message(
                db=db,
                conversation_id=voice_interaction.conversation_id,
                workspace_id=workspace_id,
                sender_type="customer",
                content=transcript
            )

            if result.agent_message:
                reply_text = result.agent_message.content
                voice_interaction.reply_text = reply_text
                await db.flush()

                try:
                    reply_audio_bytes = await tts_provider.synthesize(reply_text)
                    voice_interaction.reply_audio_bytes = reply_audio_bytes
                    voice_interaction.status = "completed"
                except Exception as tts_err:
                    logger.error(f"TTS generation failed: {tts_err}")
                    voice_interaction.error_code = "TTS_FAILED"
                    voice_interaction.error_message = str(tts_err)
                    voice_interaction.status = "completed_with_errors"
            else:
                voice_interaction.status = "completed"

            await db.commit()
            return {"status": voice_interaction.status, "voice_interaction_id": interaction_id}
            
        except Exception as e:
            await db.rollback()
            voice_interaction = await db.get(VoiceInteraction, UUID(interaction_id))
            voice_interaction.status = "failed"
            voice_interaction.error_message = str(e)
            await db.commit()
            raise
