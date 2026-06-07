import logging
from typing import Callable, Optional
from fastapi import Depends, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

async def get_public_api_key(
    request: Request,
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

    stmt = select(PublicApiKey).where(PublicApiKey.prefix == prefix, PublicApiKey.is_active == True)
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
    Dependency factory to enforce scope checks.
    """
    async def scope_checker(
        request: Request,
        api_key: PublicApiKey = Depends(get_public_api_key),
        db: AsyncSession = Depends(get_db)
    ) -> PublicApiKey:
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
