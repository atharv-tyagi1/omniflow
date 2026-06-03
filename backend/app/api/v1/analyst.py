from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.app.core.ai.rate_limiter import RateLimiter
from backend.app.core.ai.gemini_client import GeminiClient

router = APIRouter()

# Instantiate rate limiter
rate_limiter = RateLimiter()

# ========== Models ==========


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: Optional[str] = None
    error: Optional[str] = None
    remaining: Optional[Dict[str, Any]] = None


# ========== Routes ==========


@router.get("/api/limits")
async def get_limits():
    """Get current rate limit status."""
    return rate_limiter.status()


@router.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a natural language query using Gemini AI."""
    query = request.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Check rate limit
    limit_check = rate_limiter.check()
    if not limit_check["allowed"]:
        return QueryResponse(
            response=None,
            error=limit_check["error"],
            remaining=limit_check["remaining"],
        )

    # Record the request
    rate_limiter.record()

    # Call Gemini
    result = await GeminiClient.generate_analyst_response(query)

    return QueryResponse(
        response=result["response"],
        error=result["error"],
        remaining=rate_limiter.status(),
    )
