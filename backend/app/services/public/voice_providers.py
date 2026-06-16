import os
import tempfile
from abc import ABC, abstractmethod
from typing import Tuple

from backend.app.services.public.voice_storage import VoiceArtifactStorage

class BaseTranscriptionProvider(ABC):
    @abstractmethod
    async def transcribe_from_ref(self, storage: VoiceArtifactStorage, audio_ref: str, mime_type: str) -> str:
        """
        Transcribe audio from a durable artifact reference.
        """
        pass

class BaseTTSProvider(ABC):
    @abstractmethod
    async def synthesize_to_ref(self, storage: VoiceArtifactStorage, text: str) -> str:
        """
        Synthesize text and store as a durable artifact reference.
        """
        pass

class GeminiTranscriptionProvider(BaseTranscriptionProvider):
    async def transcribe_from_ref(self, storage: VoiceArtifactStorage, audio_ref: str, mime_type: str) -> str:
        import google.genai as genai
        from google.genai import types

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Read the file via storage abstraction
        audio_bytes = await storage.read_audio(audio_ref)

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                "Transcribe the following audio accurately. Reply with ONLY the transcription. Do not include any filler text or formatting.",
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            ],
        )
        return response.text.strip()

class GTTSProvider(BaseTTSProvider):
    async def synthesize_to_ref(self, storage: VoiceArtifactStorage, text: str) -> str:
        from gtts import gTTS
        
        tts = gTTS(text=text, lang="en")
        fd, path = tempfile.mkstemp(suffix=".mp3")
        
        try:
            with os.fdopen(fd, "wb") as f:
                tts.write_to_fp(f)
            
            with open(path, "rb") as f:
                audio_bytes = f.read()
                
            return await storage.save_audio(audio_bytes, prefix="tts")
        finally:
            if os.path.exists(path):
                os.remove(path)
