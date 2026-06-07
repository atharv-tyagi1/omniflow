import uuid
from typing import Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.database import get_db
from backend.app.core.public_auth import require_scope
from backend.app.core.rate_limiter import rate_limit
from backend.app.core.public_errors import PublicAPIException
from backend.app.schemas.public_api import PublicResponse
from backend.app.models.analytics import AnalyticsDailyRollup

router = APIRouter(prefix="/analytics", tags=["public_analytics"])

@router.get("/overview", response_model=PublicResponse[dict[str, Any]])
async def get_analytics_overview(
    req: Request,
    db: AsyncSession = Depends(get_db),
    api_key=Depends(require_scope("analytics_read")),
    _=Depends(rate_limit(limit=10, window_seconds=60))
):
    workspace_id = uuid.UUID(req.state.workspace_id)
    
    # Simple aggregation from AnalyticsDailyRollup
    stmt = select(
        func.sum(AnalyticsDailyRollup.total_conversations).label("total_conversations"),
        func.sum(AnalyticsDailyRollup.sales_qualified_leads).label("sales_qualified_leads"),
        func.sum(AnalyticsDailyRollup.support_tickets_created).label("support_tickets_created")
    ).where(AnalyticsDailyRollup.workspace_id == workspace_id)
    
    result = await db.execute(stmt)
    row = result.fetchone()
    
    data = {
        "total_conversations": row.total_conversations or 0,
        "sales_qualified_leads": row.sales_qualified_leads or 0,
        "support_tickets_created": row.support_tickets_created or 0
    }
    
    return PublicResponse(success=True, data=data)
