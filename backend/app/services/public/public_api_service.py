import logging
import uuid
import secrets
import bcrypt
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, asc, func

from backend.app.models.public_api import PublicApiKey, PublicApiKeyScope, PublicApiKeyRotation, PublicWebhook, PublicApiKeyAudit

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
    async def invalidate_api_key_cache(prefix: str):
        """
        Explicitly invalidate any cached auth or lookup entries.
        Ensures the new key is valid and the old key is invalid immediately.
        """
        # In a real environment with Redis/LRU, we'd clear `cache.delete(f"api_key:{prefix}")`
        # Currently, auth queries the DB directly on each request, so DB changes are instantaneous.
        pass

    @staticmethod
    async def list_api_keys(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[PublicApiKey], int]:
        stmt = select(PublicApiKey).where(PublicApiKey.workspace_id == workspace_id)
        
        if status:
            stmt = stmt.where(PublicApiKey.status == status)
        
        if search:
            stmt = stmt.where(PublicApiKey.name.ilike(f"%{search}%"))
            
        # Stable sort (newest first)
        stmt = stmt.order_by(desc(PublicApiKey.created_at))
        
        # Pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        stmt = stmt.offset((page - 1) * limit).limit(limit)
        result = await db.execute(stmt)
        
        return result.scalars().all(), total

    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
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
            prefix=prefix,
            status="active"
        )
        db.add(api_key_record)
        await db.flush()

        for scope in scopes:
            scope_record = PublicApiKeyScope(
                api_key_id=api_key_record.id,
                scope_name=scope
            )
            db.add(scope_record)
            
        audit_record = PublicApiKeyAudit(
            workspace_id=workspace_id,
            api_key_id=api_key_record.id,
            action="create",
            actor_id=user_id
        )
        db.add(audit_record)

        await db.commit()
        return plain_key

    @staticmethod
    async def rotate_api_key(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        api_key_id: uuid.UUID,
        rotated_by_user_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> str:
        """Rotates the API key. Soft revokes the old key and creates a new one preserving lineage."""
        stmt = select(PublicApiKey).where(
            PublicApiKey.id == api_key_id,
            PublicApiKey.workspace_id == workspace_id,
            PublicApiKey.status == "active"
        )
        result = await db.execute(stmt)
        old_api_key_record = result.scalar_one_or_none()

        if not old_api_key_record:
            raise ValueError("Active API Key not found")

        # Soft Revoke Old Key
        old_api_key_record.status = "revoked"
        old_api_key_record.revoked_at = datetime.now(timezone.utc)
        old_api_key_record.revoked_by = rotated_by_user_id
        
        # Generate new key material
        plain_key, new_prefix = PublicApiService._generate_key()
        new_api_key_record = PublicApiKey(
            workspace_id=workspace_id,
            name=old_api_key_record.name,
            key_hash=PublicApiService._hash_key(plain_key),
            prefix=new_prefix,
            status="active",
            rate_limit_tier=old_api_key_record.rate_limit_tier
        )
        db.add(new_api_key_record)
        await db.flush()
        
        # Copy scopes
        scope_stmt = select(PublicApiKeyScope).where(PublicApiKeyScope.api_key_id == api_key_id)
        scope_result = await db.execute(scope_stmt)
        for old_scope in scope_result.scalars().all():
            new_scope = PublicApiKeyScope(api_key_id=new_api_key_record.id, scope_name=old_scope.scope_name)
            db.add(new_scope)
        
        # Audit trail (First-class lineage)
        audit_record = PublicApiKeyAudit(
            workspace_id=workspace_id,
            api_key_id=old_api_key_record.id,
            action="rotate",
            old_api_key_id=old_api_key_record.id,
            new_api_key_id=new_api_key_record.id,
            actor_id=rotated_by_user_id,
            reason=reason
        )
        db.add(audit_record)

        # Legacy audit trail (needed for test compliance)
        rotation_record = PublicApiKeyRotation(
            workspace_id=workspace_id,
            api_key_id=old_api_key_record.id,
            old_key_prefix=old_api_key_record.prefix,
            new_key_prefix=new_prefix,
            rotated_by=rotated_by_user_id
        )
        db.add(rotation_record)
        
        await PublicApiService.invalidate_api_key_cache(old_api_key_record.prefix)
        await db.commit()
        
        return plain_key

    @staticmethod
    async def revoke_api_key(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        api_key_id: uuid.UUID,
        revoked_by_user_id: uuid.UUID
    ) -> bool:
        """Soft revokes an API key idempotently."""
        stmt = select(PublicApiKey).where(
            PublicApiKey.id == api_key_id,
            PublicApiKey.workspace_id == workspace_id
        )
        result = await db.execute(stmt)
        api_key_record = result.scalar_one_or_none()

        if not api_key_record:
            return False
            
        if api_key_record.status == "revoked":
            return True # Idempotent

        api_key_record.status = "revoked"
        api_key_record.revoked_at = datetime.now(timezone.utc)
        api_key_record.revoked_by = revoked_by_user_id
        
        audit_record = PublicApiKeyAudit(
            workspace_id=workspace_id,
            api_key_id=api_key_record.id,
            action="revoke",
            actor_id=revoked_by_user_id
        )
        db.add(audit_record)
        
        await PublicApiService.invalidate_api_key_cache(api_key_record.prefix)
        await db.commit()
        return True

    @staticmethod
    async def get_webhook_source(db: AsyncSession, workspace_id: uuid.UUID, source: str) -> PublicWebhook:
        stmt = select(PublicWebhook).where(
            PublicWebhook.workspace_id == workspace_id,
            PublicWebhook.source == source
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
