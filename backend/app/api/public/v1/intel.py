import uuid
from typing import Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.database import get_db
from backend.app.core.public_auth import require_scope
from backend.app.core.rate_limiter import rate_limit
from backend.app.schemas.public_api import PublicResponse
from backend.app.models.intel_rollups import IntelDailyTopicRollup

router = APIRouter(prefix="/intel", tags=["public_intel"])

@router.get("/topics", response_model=PublicResponse[list[dict[str, Any]]])
async def get_intel_topics(
    req: Request,
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("intel_read")),
    _=Depends(rate_limit(limit=10, window_seconds=60))
):
    workspace_id = uuid.UUID(req.state.workspace_id)
    
    # Simple aggregation of top topics
    stmt = select(
        IntelDailyTopicRollup.topic_id,
        IntelDailyTopicRollup.topic_name,
        func.sum(IntelDailyTopicRollup.mention_count).label("mentions")
    ).where(
        IntelDailyTopicRollup.workspace_id == workspace_id
    ).group_by(
        IntelDailyTopicRollup.topic_id,
        IntelDailyTopicRollup.topic_name
    ).order_by(
        func.sum(IntelDailyTopicRollup.mention_count).desc()
    ).limit(10)
    
    result = await db.execute(stmt)
    rows = result.fetchall()
    
    data = [
        {
            "topic_id": row.topic_id,
            "topic_name": row.topic_name,
            "mentions": row.mentions
        } for row in rows
    ]
    
    return PublicResponse(success=True, data=data)
