import time
import logging
from typing import Optional
from fastapi import Request, Depends
from functools import wraps

from backend.app.core.config import settings
from backend.app.core.public_errors import PublicAPIException
from backend.app.core.telemetry import log_public_telemetry

logger = logging.getLogger(__name__)

# Very simple sliding window for development fallback
_in_memory_limits = {}

def get_redis_client():
    if settings.ENVIRONMENT == "production":
        import redis.asyncio as redis
        # Replace with actual config
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        return redis.from_url(redis_url, decode_responses=True)
    return None

async def check_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """
    Returns True if allowed, False if rate limited.
    """
    if getattr(settings, "ENVIRONMENT", "development") == "production":
        redis = get_redis_client()
        if redis:
            try:
                current_time = int(time.time())
                window_start = current_time - window_seconds
                
                # ZREMRANGEBYSCORE key 0 window_start
                await redis.zremrangebyscore(key, 0, window_start)
                
                # ZCARD key
                count = await redis.zcard(key)
                
                if count >= limit:
                    return False
                    
                # ZADD key {current_time} {current_time}
                await redis.zadd(key, {str(current_time): current_time})
                await redis.expire(key, window_seconds)
                return True
            except Exception as e:
                logger.error(f"Redis rate limiting failed: {e}")
                # Degrade gracefully if redis is down
                return True
                
    # Development In-Memory implementation
    current_time = time.time()
    if key not in _in_memory_limits:
        _in_memory_limits[key] = []
        
    _in_memory_limits[key] = [t for t in _in_memory_limits[key] if t > current_time - window_seconds]
    if len(_in_memory_limits[key]) >= limit:
        return False
        
    _in_memory_limits[key].append(current_time)
    return True

def rate_limit(limit: int, window_seconds: int = 60):
    """
    Dependency / decorator for rate limiting per API key and route.
    Expects request.state.api_key_id to be set by the auth dependency.
    """
    async def rate_limit_dependency(request: Request):
        api_key_id = getattr(request.state, "api_key_id", "anonymous")
        route_path = request.url.path
        rate_key = f"rate_limit:{api_key_id}:{route_path}"
        
        allowed = await check_rate_limit(rate_key, limit, window_seconds)
        if not allowed:
            workspace_id = getattr(request.state, "workspace_id", "unknown")
            logger.warning(f"Rate limit exceeded for API Key {api_key_id} in workspace {workspace_id} on {route_path}")
            log_public_telemetry(
                "public_rate_limit_exceeded",
                workspace_id=workspace_id if workspace_id != "unknown" else None,
                api_key_id=api_key_id,
                details={"route": route_path, "limit": limit, "window_seconds": window_seconds}
            )
            raise PublicAPIException(
                "Too many requests. Please slow down.",
                status_code=429,
                code="RATE_LIMIT_EXCEEDED"
            )
            
    return rate_limit_dependency
