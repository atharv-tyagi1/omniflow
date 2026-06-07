import logging
import asyncio
from typing import Callable, Optional
from fastapi import Depends, Request, Security, BackgroundTasks
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
import bcrypt

from backend.app.core.database import get_db
from backend.app.models.public_api import PublicApiKey, PublicApiKeyScope
from backend.app.core.public_errors import PublicAPIException
from backend.app.core.telemetry import log_public_telemetry, LatencyTracker

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)

async def verify_api_key_hash(plain_key: str, hashed_key: str) -> bool:
    """Verifies an API key against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_key.encode('utf-8'), hashed_key.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying API key hash: {e}")
        return False

async def _record_usage_async(api_key_id: str, ip: str, user_agent: str):
    """
    Best-effort usage tracking helper. Runs outside the critical auth path.
    Never fails the main API request.
    """
    try:
        # Import sessionmaker locally to avoid circular imports or dependency on request cycle
        import uuid
        from backend.app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            stmt = (
                update(PublicApiKey)
                .where(PublicApiKey.id == uuid.UUID(api_key_id))
                .values(
                    request_count=PublicApiKey.request_count + 1,
                    last_ip=ip,
                    last_user_agent=user_agent,
                    last_used_at=func.now()
                )
            )
            await db.execute(stmt)
            await db.commit()
    except Exception as e:
        logger.error(f"Failed to record API key usage for {api_key_id}: {e}")

async def get_public_api_key(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> PublicApiKey:
    """
    Dependency to authenticate the external client via X-Api-Key.
    It expects keys in the format of {prefix}_{random_string} (e.g., of_live_1a2b3c4d...).
    """
    if not api_key:
        raise PublicAPIException("Missing X-Api-Key header", status_code=401, code="UNAUTHORIZED")

    tracker = LatencyTracker()
    prefix = api_key[:8]
    if len(prefix) < 8:
        log_public_telemetry(
            "public_auth_failure",
            details={"reason": "invalid_format", "prefix_attempt": prefix}
        )
        raise PublicAPIException("Invalid API Key format", status_code=401, code="UNAUTHORIZED")

    # Only accept active keys
    stmt = select(PublicApiKey).where(PublicApiKey.prefix == prefix, PublicApiKey.status == "active")
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    for candidate in candidates:
        if await verify_api_key_hash(api_key, candidate.key_hash):
            log_public_telemetry(
                "public_auth_success",
                workspace_id=str(candidate.workspace_id),
                api_key_id=str(candidate.id),
                latency_ms=tracker.get_latency_ms()
            )
            
            # Non-blocking best-effort usage tracking
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            background_tasks.add_task(_record_usage_async, str(candidate.id), client_ip, user_agent)
            
            return candidate

    logger.warning("Failed API Key authentication attempt.")
    log_public_telemetry(
        "public_auth_failure",
        details={"reason": "invalid_or_inactive_key", "prefix": prefix},
        latency_ms=tracker.get_latency_ms()
    )
    raise PublicAPIException("Invalid or inactive API Key", status_code=401, code="UNAUTHORIZED")

def require_scope(required_scope: str) -> Callable:
    """
    Dependency factory to enforce scope checks canonically against PublicApiKeyScope.
    """
    async def scope_checker(
        request: Request,
        api_key: PublicApiKey = Depends(get_public_api_key),
        db: AsyncSession = Depends(get_db)
    ) -> PublicApiKey:
        # Enforce canonical scope mapping
        stmt = select(PublicApiKeyScope).where(
            PublicApiKeyScope.api_key_id == api_key.id,
            PublicApiKeyScope.scope_name == required_scope
        )
        result = await db.execute(stmt)
        scope = result.scalar_one_or_none()

        if not scope:
            logger.warning(f"API Key {api_key.id} attempted to access {request.url.path} without scope {required_scope}")
            log_public_telemetry(
                "public_scope_failure",
                workspace_id=str(api_key.workspace_id),
                api_key_id=str(api_key.id),
                details={"required_scope": required_scope, "path": request.url.path}
            )
            raise PublicAPIException(f"Missing required scope: {required_scope}", status_code=403, code="FORBIDDEN")
        
        # Attach the workspace_id to request state for rate limiting and generic context
        request.state.workspace_id = str(api_key.workspace_id)
        request.state.api_key_id = str(api_key.id)
        
        return api_key

    return scope_checker
