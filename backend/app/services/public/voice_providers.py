import os
import tempfile
from abc import ABC, abstractmethod
from typing import Tuple

class BaseTranscriptionProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        """
        Transcribe audio bytes to text.
        """
        pass

class BaseTTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize text to audio bytes.
        """
        pass

class GeminiTranscriptionProvider(BaseTranscriptionProvider):
    async def transcribe(self, audio_bytes: bytes, mime_type: str) -> str:
        import google.genai as genai
        from google.genai import types

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

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
    async def synthesize(self, text: str) -> bytes:
        from gtts import gTTS
        
        tts = gTTS(text=text, lang="en")
        fd, path = tempfile.mkstemp(suffix=".mp3")
        
        try:
            with os.fdopen(fd, "wb") as f:
                tts.write_to_fp(f)
            
            with open(path, "rb") as f:
                audio_bytes = f.read()
                
            return audio_bytes
        finally:
            if os.path.exists(path):
                os.remove(path)
