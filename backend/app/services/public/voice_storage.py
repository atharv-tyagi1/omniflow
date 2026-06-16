import os
import uuid
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from datetime import datetime, timezone

from fastapi import UploadFile


class VoiceArtifactStorage(ABC):
    """
    Abstract interface for durable voice artifact storage.
    Ensures the voice pipeline does not depend on local file paths.
    """

    @abstractmethod
    async def stage_upload(self, upload_file: UploadFile) -> Tuple[str, str, int]:
        """
        Stages an HTTP UploadFile incrementally.
        Returns (artifact_ref, sha256_hash, size_in_bytes).
        """
        pass

    @abstractmethod
    async def save_audio(self, audio_bytes: bytes, prefix: str = "tts") -> str:
        """
        Saves raw audio bytes and returns a durable artifact reference.
        Used primarily for TTS output or external downloads.
        """
        pass

    @abstractmethod
    async def read_audio(self, artifact_ref: str) -> bytes:
        """
        Reads the audio bytes from the durable artifact reference.
        """
        pass

    @abstractmethod
    async def delete_artifact(self, artifact_ref: str) -> bool:
        """
        Deletes the artifact. Returns True if deleted, False if not found.
        """
        pass


class LocalVoiceStorage(VoiceArtifactStorage):
    """
    Local filesystem implementation of VoiceArtifactStorage.
    """

    def __init__(self, storage_dir: str = "/tmp/omniflow_voice_artifacts"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    async def stage_upload(self, upload_file: UploadFile) -> Tuple[str, str, int]:
        artifact_id = str(uuid.uuid4())
        ext = upload_file.filename.split('.')[-1] if upload_file.filename and '.' in upload_file.filename else 'raw'
        filename = f"upload_{artifact_id}.{ext}"
        filepath = os.path.join(self.storage_dir, filename)

        import hashlib
        sha256 = hashlib.sha256()
        size = 0
        chunk_size = 64 * 1024  # 64KB

        # Ensure we're at the start of the file
        await upload_file.seek(0)
        
        with open(filepath, "wb") as out_file:
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                sha256.update(chunk)
                size += len(chunk)
        
        # Reset file pointer for any downstream users (though they should use the ref)
        await upload_file.seek(0)

        # The filepath acts as the artifact_ref for the local implementation
        return filepath, sha256.hexdigest(), size

    async def save_audio(self, audio_bytes: bytes, prefix: str = "tts") -> str:
        artifact_id = str(uuid.uuid4())
        filename = f"{prefix}_{artifact_id}.raw"
        filepath = os.path.join(self.storage_dir, filename)

        with open(filepath, "wb") as out_file:
            out_file.write(audio_bytes)

        return filepath

    async def read_audio(self, artifact_ref: str) -> bytes:
        if not os.path.exists(artifact_ref):
            raise FileNotFoundError(f"Artifact not found: {artifact_ref}")
            
        with open(artifact_ref, "rb") as f:
            return f.read()

    async def delete_artifact(self, artifact_ref: str) -> bool:
        if os.path.exists(artifact_ref):
            try:
                os.remove(artifact_ref)
                return True
            except OSError:
                return False
        return False
