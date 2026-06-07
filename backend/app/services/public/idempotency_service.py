import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.app.models.public_api import IdempotencyKey, PublicAsyncJob
from backend.app.core.public_errors import PublicAPIException
from backend.app.core.telemetry import log_public_telemetry
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class IdempotencyService:
    @staticmethod
    async def get_or_create_idempotency_key(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        key: str,
        path: str,
        retention_days: int = 30
    ) -> tuple[IdempotencyKey, bool]:
        """
        Returns (IdempotencyKey, is_new).
        If the key already exists for this workspace, is_new=False.
        """
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.workspace_id == workspace_id,
            IdempotencyKey.idempotency_key == key
        )
        result = await db.execute(stmt)
        existing_record = result.scalar_one_or_none()

        if existing_record:
            if existing_record.status == "in_progress":
                raise PublicAPIException("Concurrent request in progress", status_code=409, code="CONCURRENT_REQUEST")
            
            log_public_telemetry(
                "public_idempotency_hit",
                workspace_id=str(workspace_id),
                details={"key": key, "path": path}
            )
            return existing_record, False

        # Create new record
        retention = getattr(settings, "IDEMPOTENCY_RETENTION_DAYS", retention_days)
        expires_at = datetime.now(timezone.utc) + timedelta(days=retention)
        new_record = IdempotencyKey(
            workspace_id=workspace_id,
            idempotency_key=key,
            path=path,
            status="in_progress",
            expires_at=expires_at
        )
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        return new_record, True

    @staticmethod
    async def complete_idempotency_request(
        db: AsyncSession,
        record: IdempotencyKey,
        response_body: Any
    ):
        """Mark idempotency request as completed and save response."""
        record.status = "completed"
        record.response_body = response_body
        await db.commit()

    @staticmethod
    async def fail_idempotency_request(
        db: AsyncSession,
        record: IdempotencyKey
    ):
        """Mark idempotency request as failed."""
        record.status = "failed"
        await db.commit()

    @staticmethod
    async def cleanup_expired_keys(db: AsyncSession):
        """Background job helper to delete expired idempotency keys."""
        try:
            now = datetime.now(timezone.utc)
            stmt = delete(IdempotencyKey).where(IdempotencyKey.expires_at < now)
            result = await db.execute(stmt)
            await db.commit()
            if result.rowcount > 0:
                logger.info(f"Cleaned up {result.rowcount} expired idempotency keys")
                log_public_telemetry("public_idempotency_cleanup", details={"count": result.rowcount})
        except Exception as e:
            logger.error(f"Error cleaning up idempotency keys: {e}")
            await db.rollback()

    @staticmethod
    async def cleanup_expired_async_jobs(db: AsyncSession):
        """Background job helper to delete explicitly expired terminal async jobs."""
        try:
            now = datetime.now(timezone.utc)
            stmt = delete(PublicAsyncJob).where(
                PublicAsyncJob.expires_at < now,
                PublicAsyncJob.status.in_(["completed", "failed"])
            )
            result = await db.execute(stmt)
            await db.commit()
            if result.rowcount > 0:
                logger.info(f"Cleaned up {result.rowcount} expired async jobs")
                log_public_telemetry("public_async_job_cleanup", details={"count": result.rowcount})
        except Exception as e:
            logger.error(f"Error cleaning up async jobs: {e}")
            await db.rollback()
