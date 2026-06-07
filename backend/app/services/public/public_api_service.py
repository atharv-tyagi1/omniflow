import logging
import uuid
import secrets
import bcrypt
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.public_api import PublicApiKey, PublicApiKeyScope, PublicApiKeyRotation, PublicWebhook

logger = logging.getLogger(__name__)

class PublicApiService:
    @staticmethod
    def _hash_key(plain_key: str) -> str:
        return bcrypt.hashpw(plain_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def _generate_key() -> tuple[str, str]:
        """Returns (plain_key, prefix)"""
        random_part = secrets.token_urlsafe(32)
        plain_key = f"of_live_{random_part}"
        prefix = plain_key[:8] # 'of_live_'
        return plain_key, prefix

    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        name: str,
        scopes: list[str]
    ) -> str:
        """Returns the plaintext API key (only shown once to the user)."""
        plain_key, prefix = PublicApiService._generate_key()
        key_hash = PublicApiService._hash_key(plain_key)

        api_key_record = PublicApiKey(
            workspace_id=workspace_id,
            name=name,
            key_hash=key_hash,
            prefix=prefix
        )
        db.add(api_key_record)
        await db.flush()

        for scope in scopes:
            scope_record = PublicApiKeyScope(
                api_key_id=api_key_record.id,
                scope_name=scope
            )
            db.add(scope_record)

        await db.commit()
        return plain_key

    @staticmethod
    async def rotate_api_key(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        api_key_id: uuid.UUID,
        rotated_by_user_id: uuid.UUID
    ) -> str:
        """Rotates the API key and returns the new plaintext key. Records rotation audit."""
        stmt = select(PublicApiKey).where(
            PublicApiKey.id == api_key_id,
            PublicApiKey.workspace_id == workspace_id
        )
        result = await db.execute(stmt)
        api_key_record = result.scalar_one_or_none()

        if not api_key_record:
            raise ValueError("API Key not found")

        old_prefix = api_key_record.prefix
        
        # Generate new key material
        plain_key, new_prefix = PublicApiService._generate_key()
        api_key_record.key_hash = PublicApiService._hash_key(plain_key)
        api_key_record.prefix = new_prefix
        
        # Audit trail
        rotation_record = PublicApiKeyRotation(
            workspace_id=workspace_id,
            api_key_id=api_key_id,
            old_key_prefix=old_prefix,
            new_key_prefix=new_prefix,
            rotated_by=rotated_by_user_id
        )
        db.add(rotation_record)
        await db.commit()
        
        return plain_key

    @staticmethod
    async def get_webhook_source(db: AsyncSession, workspace_id: uuid.UUID, source: str) -> PublicWebhook:
        stmt = select(PublicWebhook).where(
            PublicWebhook.workspace_id == workspace_id,
            PublicWebhook.source == source
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
