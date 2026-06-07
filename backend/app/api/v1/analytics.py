"""
Phase 12: Analytics Dashboard API endpoints.

All endpoints are workspace-scoped, require authentication and workspace
membership. Dates are normalized to UTC. Responses use a standardized
envelope with freshness metadata.

AnalyticsService is the single source of truth — no duplicate metric logic.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from typing import Optional

from backend.app.core.database import get_db
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id, require_manager
from backend.app.models.user import User
from backend.app.services.analytics.service import AnalyticsService
from backend.app.schemas.analytics import AnalyticsGranularity

router = APIRouter()


# ──────────────────────────────────────────────────────────
# Shared query parameters
# ──────────────────────────────────────────────────────────

async def _common_params(
    start_date: Optional[datetime] = Query(None, description="Start date (UTC ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End date (UTC ISO 8601)"),
    granularity: AnalyticsGranularity = Query(AnalyticsGranularity.DAILY, description="Trend granularity"),
):
    return {"start_date": start_date, "end_date": end_date, "granularity": granularity}


# ──────────────────────────────────────────────────────────
# Legacy dashboard endpoint (preserved for backward compat)
# ──────────────────────────────────────────────────────────

@router.get("/dashboard")
async def get_dashboard_data(
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Legacy dashboard endpoint. Delegates to AnalyticsService.get_overview
    for consistency (single source of truth).
    """
    try:
        result = await AnalyticsService.get_overview(db, workspace_id)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────
# Phase 12 Dashboard API endpoints
# ──────────────────────────────────────────────────────────

@router.get("/overview")
async def get_analytics_overview(
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: AnalyticsGranularity = Query(AnalyticsGranularity.DAILY),
):
    """Overview KPIs and conversation trends."""
    result = await AnalyticsService.get_overview(db, workspace_id, start_date, end_date, granularity)
    return result.model_dump()


@router.get("/conversations")
async def get_analytics_conversations(
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: AnalyticsGranularity = Query(AnalyticsGranularity.DAILY),
):
    """Conversation metrics: total, active, resolved + trends."""
    result = await AnalyticsService.get_conversations(db, workspace_id, start_date, end_date, granularity)
    return result.model_dump()


@router.get("/sales")
async def get_analytics_sales(
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: AnalyticsGranularity = Query(AnalyticsGranularity.DAILY),
):
    """Sales metrics: leads created, qualified, funnel distribution."""
    result = await AnalyticsService.get_sales(db, workspace_id, start_date, end_date, granularity)
    return result.model_dump()


@router.get("/support")
async def get_analytics_support(
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: AnalyticsGranularity = Query(AnalyticsGranularity.DAILY),
):
    """Support metrics: tickets created, resolved, open."""
    result = await AnalyticsService.get_support(db, workspace_id, start_date, end_date, granularity)
    return result.model_dump()


@router.get("/customer-care")
async def get_analytics_customer_care(
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: AnalyticsGranularity = Query(AnalyticsGranularity.DAILY),
):
    """Customer care metrics: complaints, refunds, escalations."""
    result = await AnalyticsService.get_customer_care(db, workspace_id, start_date, end_date, granularity)
    return result.model_dump()


@router.get("/handoffs")
async def get_analytics_handoffs(
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: AnalyticsGranularity = Query(AnalyticsGranularity.DAILY),
):
    """Handoff metrics: total, failed, loop prevention triggers."""
    result = await AnalyticsService.get_handoffs(db, workspace_id, start_date, end_date, granularity)
    return result.model_dump()


@router.get("/trends")
async def get_analytics_trends(
    metric: str = Query(..., description="Metric name (from AnalyticsMetricName enum)"),
    workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: AnalyticsGranularity = Query(AnalyticsGranularity.DAILY),
    days: int = Query(7, ge=1, le=90),
):
    """Generic trend endpoint for any metric."""
    result = await AnalyticsService.get_trends(db, workspace_id, metric, start_date, end_date, granularity, days)
    return result.model_dump()
