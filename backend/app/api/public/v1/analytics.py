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
    
    from backend.app.services.analytics.service import AnalyticsService
    from backend.app.schemas.analytics import AnalyticsMetricName

    total_conv = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.TOTAL_CONVERSATIONS)
    leads_qual = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.LEADS_QUALIFIED)
    tickets_created = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.TICKETS_CREATED)
    
    data = {
        "total_conversations": total_conv,
        "sales_qualified_leads": leads_qual,
        "support_tickets_created": tickets_created
    }
    
    return PublicResponse(success=True, data=data)
