import logging
import httpx
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.services.conversation_service import ConversationService
from backend.app.models.voice_interaction import VoiceInteraction
from backend.app.core.ai.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class TelegramService:
    @staticmethod
    def _get_bot_token() -> str:
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not configured")
        return token

    @staticmethod
    def _get_api_url(method: str) -> str:
        return f"https://api.telegram.org/bot{TelegramService._get_bot_token()}/{method}"

    @staticmethod
    def _get_file_url(file_path: str) -> str:
        return f"https://api.telegram.org/file/bot{TelegramService._get_bot_token()}/{file_path}"

    @staticmethod
    async def setup_webhook() -> bool:
        """Register the webhook with Telegram."""
        if not settings.TELEGRAM_WEBHOOK_URL or not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram webhook URL or Token not configured, skipping setup.")
            return False
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    TelegramService._get_api_url("setWebhook"),
                    json={"url": settings.TELEGRAM_WEBHOOK_URL}
                )
                data = response.json()
                if data.get("ok"):
                    logger.info(f"Telegram webhook set successfully: {settings.TELEGRAM_WEBHOOK_URL}")
                    return True
                else:
                    logger.error(f"Failed to set Telegram webhook: {data.get('description')}")
                    return False
            except Exception as e:
                logger.error(f"Exception setting Telegram webhook: {e}")
                return False

    @staticmethod
    async def send_message(chat_id: int, text: str) -> bool:
        """Send a text message back to the user via Telegram Bot API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    TelegramService._get_api_url("sendMessage"),
                    json={
                        "chat_id": chat_id,
                        "text": text
                    }
                )
                return response.json().get("ok", False)
            except Exception as e:
                logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
                return False

    @staticmethod
    async def send_voice_message(chat_id: int, text: str) -> bool:
        """Generate TTS from text and send it as a voice note via Telegram."""
        import tempfile
        import os
        from gtts import gTTS

        # 1. Generate audio file
        try:
            tts = gTTS(text=text, lang='en')
            fd, path = tempfile.mkstemp(suffix=".ogg")
            with os.fdopen(fd, 'wb') as f:
                tts.write_to_fp(f)
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return await TelegramService.send_message(chat_id, text)

        # 2. Upload and send
        try:
            async with httpx.AsyncClient() as client:
                with open(path, "rb") as audio_file:
                    files = {"voice": ("voice.ogg", audio_file, "audio/ogg")}
                    data = {"chat_id": str(chat_id)}
                    response = await client.post(
                        TelegramService._get_api_url("sendVoice"),
                        data=data,
                        files=files
                    )
                os.remove(path)
                return response.json().get("ok", False)
        except Exception as e:
            logger.error(f"Failed to send Telegram voice message to {chat_id}: {e}")
            if os.path.exists(path):
                os.remove(path)
            # Fallback to text
            return await TelegramService.send_message(chat_id, text)

    @staticmethod
    async def _resolve_conversation(
        db: AsyncSession, 
        telegram_id: str, 
        name: str, 
        channel: str = "telegram_chat"
    ) -> tuple[Any, Any]:
        """Resolves the customer and active conversation."""
        workspace_id = UUID(settings.DEFAULT_WORKSPACE_ID) if settings.DEFAULT_WORKSPACE_ID else None
        if not workspace_id:
            raise ValueError("DEFAULT_WORKSPACE_ID is not configured")

        customer = await CustomerRepository.get_or_create_by_telegram_id(
            db=db,
            telegram_id=telegram_id,
            name=name,
            workspace_id=workspace_id
        )

        conversation = await ConversationRepository.get_active_by_customer(
            db=db,
            customer_id=customer.id,
            channel=channel
        )

        if not conversation:
            conversation = await ConversationService.create_conversation(
                db=db,
                workspace_id=workspace_id,
                customer_id=customer.id,
                channel=channel
            )
            
        return customer, conversation

    @staticmethod
    async def handle_text_message(db: AsyncSession, message: dict) -> None:
        """Process an incoming text message from Telegram."""
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        sender_first_name = message.get("from", {}).get("first_name", "Telegram User")
        telegram_id = str(message.get("from", {}).get("id"))

        if not chat_id or not text or not telegram_id:
            return

        # Basic command handling
        if text.startswith("/start") or text.startswith("/help"):
            await TelegramService.send_message(
                chat_id, 
                "Welcome to OmniFlow! How can I help you today?"
            )
            return

        try:
            customer, conversation = await TelegramService._resolve_conversation(
                db=db, telegram_id=telegram_id, name=sender_first_name, channel="telegram_chat"
            )

            # Pass user message to conversation pipeline
            await ConversationService.add_message(
                db=db,
                conversation_id=conversation.id,
                workspace_id=customer.workspace_id,
                sender_type="customer",
                content=text
            )

            # Fetch the latest message (agent's reply)
            history = await ConversationService.list_messages(
                db=db, conversation_id=conversation.id, workspace_id=customer.workspace_id
            )
            if history:
                latest = history[-1]
                if latest.sender_type != "customer":
                    await TelegramService.send_message(chat_id, latest.content)

        except Exception as e:
            logger.error(f"Error handling Telegram text message: {e}")
            await TelegramService.send_message(chat_id, "I'm sorry, I'm having trouble processing that right now.")

    @staticmethod
    async def handle_voice_message(db: AsyncSession, message: dict) -> None:
        """Process an incoming voice message from Telegram."""
        chat_id = message.get("chat", {}).get("id")
        voice_info = message.get("voice", {})
        file_id = voice_info.get("file_id")
        duration = voice_info.get("duration", 0)
        sender_first_name = message.get("from", {}).get("first_name", "Telegram User")
        telegram_id = str(message.get("from", {}).get("id"))

        if not chat_id or not file_id or not telegram_id:
            return

        try:
            # 1. Get file path from Telegram
            async with httpx.AsyncClient() as client:
                file_info_resp = await client.get(
                    TelegramService._get_api_url("getFile"),
                    params={"file_id": file_id}
                )
                file_info = file_info_resp.json()
                if not file_info.get("ok"):
                    logger.error("Failed to get voice file path from Telegram")
                    return
                
                file_path = file_info["result"]["file_path"]
                file_url = TelegramService._get_file_url(file_path)
                
                # Download the actual audio bytes
                audio_resp = await client.get(file_url)
                audio_data = audio_resp.content

            # 2. Use Gemini to transcribe
            gemini = GeminiClient.get_instance()
            # We use flash-2.0 to transcribe audio. We pass it the raw bytes.
            from google.genai import types
            
            transcript = "Could not transcribe audio."
            try:
                # Assuming GeminiClient exposes the raw client or we instantiate directly
                import os
                from google import genai
                api_key = os.environ.get("GEMINI_API_KEY")
                genai_client = genai.Client(api_key=api_key)
                
                response = genai_client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[
                        "Transcribe the following audio accurately. Reply with ONLY the transcription.",
                        types.Part.from_bytes(data=audio_data, mime_type='audio/ogg')
                    ]
                )
                transcript = response.text.strip()
            except Exception as e:
                logger.error(f"Gemini transcription failed: {e}")
                await TelegramService.send_message(chat_id, "Sorry, I couldn't understand the voice note.")
                return

            # 3. Resolve customer/conversation
            customer, conversation = await TelegramService._resolve_conversation(
                db=db, telegram_id=telegram_id, name=sender_first_name, channel="telegram_voice"
            )

            # 4. Save VoiceInteraction record
            voice_record = VoiceInteraction(
                conversation_id=conversation.id,
                audio_url=file_url,
                transcript=transcript,
                duration_seconds=duration
            )
            db.add(voice_record)
            await db.flush()

            # 5. Process through agent pipeline
            await ConversationService.add_message(
                db=db,
                conversation_id=conversation.id,
                workspace_id=customer.workspace_id,
                sender_type="customer",
                content=transcript
            )

            # 6. Fetch agent reply and send back
            history = await ConversationService.list_messages(
                db=db, conversation_id=conversation.id, workspace_id=customer.workspace_id
            )
            if history:
                latest = history[-1]
                if latest.sender_type != "customer":
                    await TelegramService.send_voice_message(chat_id, latest.content)

        except Exception as e:
            logger.error(f"Error handling Telegram voice message: {e}")
            await TelegramService.send_message(chat_id, "I'm sorry, I encountered an error processing your voice note.")
