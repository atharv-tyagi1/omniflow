"""
Phase 12: AnalyticsService — Single Source of Truth for Metrics.

All dashboard APIs, UI pages, and future phases (13: Conversation Intel,
14: Business Analyst) consume metrics exclusively through this service.

DashboardService is now a thin wrapper that delegates here.
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.analytics import (
    AnalyticsEvent,
    AnalyticsHourlyRollup,
    AnalyticsDailyRollup,
    AnalyticsOutbox,
)
from backend.app.schemas.analytics import (
    AnalyticsMetricName,
    AnalyticsEventType,
    AnalyticsGranularity,
    AnalyticsFreshness,
    AnalyticsResponseEnvelope,
    KPI,
    ChartDataPoint,
    AnalyticsOverviewResponse,
    AnalyticsConversationsResponse,
    AnalyticsSalesResponse,
    AnalyticsSupportResponse,
    AnalyticsCustomerCareResponse,
    AnalyticsHandoffsResponse,
)

logger = logging.getLogger(__name__)

# Default lookback window for trend queries
DEFAULT_TREND_DAYS = 7


class AnalyticsService:
    """
    Single source of truth for all analytics queries. Reads from rollup
    tables for performance. Never scans raw event tables for dashboard loads.
    """

    # ──────────────────────────────────────────────────────────
    # Freshness helper
    # ──────────────────────────────────────────────────────────
    @staticmethod
    async def _get_freshness(db: AsyncSession, workspace_id: UUID) -> AnalyticsFreshness:
        """Compute freshness metadata for the response envelope."""
        now = datetime.now(timezone.utc)

        # Last ingested event time
        stmt = (
            select(func.max(AnalyticsEvent.created_at))
            .where(AnalyticsEvent.workspace_id == workspace_id)
        )
        last_ingested = await db.scalar(stmt)

        # Pending outbox lag
        pending_stmt = (
            select(func.min(AnalyticsOutbox.created_at))
            .where(
                AnalyticsOutbox.workspace_id == workspace_id,
                AnalyticsOutbox.status == "pending",
            )
        )
        oldest_pending = await db.scalar(pending_stmt)

        lag = 0
        if oldest_pending:
            lag = int((now - oldest_pending).total_seconds())

        return AnalyticsFreshness(
            as_of=now,
            last_ingested_at=last_ingested,
            rollup_lag_seconds=lag,
        )

    # ──────────────────────────────────────────────────────────
    # Internal rollup query helpers
    # ──────────────────────────────────────────────────────────
    @staticmethod
    async def _get_metric_total(
        db: AsyncSession,
        workspace_id: UUID,
        metric_name: AnalyticsMetricName,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> int:
        """Sum a metric from daily rollups within the date range."""
        filters = [
            AnalyticsDailyRollup.workspace_id == workspace_id,
            AnalyticsDailyRollup.metric_name == metric_name.value,
        ]
        if start:
            filters.append(AnalyticsDailyRollup.time_bucket >= start)
        if end:
            filters.append(AnalyticsDailyRollup.time_bucket <= end)

        stmt = select(func.coalesce(func.sum(AnalyticsDailyRollup.value), 0)).where(*filters)
        result = await db.scalar(stmt)
        return int(result or 0)

    @staticmethod
    async def _get_trend(
        db: AsyncSession,
        workspace_id: UUID,
        metric_name: AnalyticsMetricName,
        days: int = DEFAULT_TREND_DAYS,
        granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY,
    ) -> List[ChartDataPoint]:
        """Get time-series data points for the specified metric."""
        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

        if granularity == AnalyticsGranularity.HOURLY:
            model = AnalyticsHourlyRollup
        else:
            model = AnalyticsDailyRollup

        stmt = (
            select(model.time_bucket, model.value)
            .where(
                model.workspace_id == workspace_id,
                model.metric_name == metric_name.value,
                model.time_bucket >= start,
            )
            .order_by(model.time_bucket.asc())
        )
        result = await db.execute(stmt)
        rows = result.all()

        return [
            ChartDataPoint(
                date=row[0].strftime("%Y-%m-%d" if granularity == AnalyticsGranularity.DAILY else "%Y-%m-%dT%H:00"),
                value=int(row[1]),
            )
            for row in rows
        ]

    @staticmethod
    async def _compute_trend_pct(
        db: AsyncSession,
        workspace_id: UUID,
        metric_name: AnalyticsMetricName,
    ) -> Optional[float]:
        """Compare current period vs previous period of equal length."""
        now = datetime.now(timezone.utc)
        period_end = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        period_start = period_end - timedelta(days=DEFAULT_TREND_DAYS)
        prev_start = period_start - timedelta(days=DEFAULT_TREND_DAYS)

        current = await AnalyticsService._get_metric_total(db, workspace_id, metric_name, period_start, period_end)
        previous = await AnalyticsService._get_metric_total(db, workspace_id, metric_name, prev_start, period_start)

        if previous == 0:
            return None
        return round(((current - previous) / previous) * 100, 1)

    # ──────────────────────────────────────────────────────────
    # Public Dashboard Methods
    # ──────────────────────────────────────────────────────────
    @staticmethod
    async def get_overview(
        db: AsyncSession,
        workspace_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY,
    ) -> AnalyticsResponseEnvelope:
        """Overview dashboard: top-level KPIs and conversation trend."""
        freshness = await AnalyticsService._get_freshness(db, workspace_id)

        conversations = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.TOTAL_CONVERSATIONS, start_date, end_date)
        resolved = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.RESOLVED_CONVERSATIONS, start_date, end_date)
        handoffs = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.TOTAL_HANDOFFS, start_date, end_date)
        escalations = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.ESCALATIONS, start_date, end_date)

        conv_trend = await AnalyticsService._compute_trend_pct(db, workspace_id, AnalyticsMetricName.TOTAL_CONVERSATIONS)
        trends = await AnalyticsService._get_trend(db, workspace_id, AnalyticsMetricName.TOTAL_CONVERSATIONS, granularity=granularity)

        data = AnalyticsOverviewResponse(
            kpis={
                "total_conversations": KPI(label="Total Conversations", value=conversations, trend=conv_trend),
                "resolved_conversations": KPI(label="Resolved", value=resolved),
                "total_handoffs": KPI(label="Handoffs", value=handoffs),
                "escalations": KPI(label="Escalations", value=escalations),
            },
            trends=trends,
        )
        return AnalyticsResponseEnvelope(data=data, freshness=freshness)

    @staticmethod
    async def get_conversations(
        db: AsyncSession,
        workspace_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY,
    ) -> AnalyticsResponseEnvelope:
        freshness = await AnalyticsService._get_freshness(db, workspace_id)
        total = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.TOTAL_CONVERSATIONS, start_date, end_date)
        resolved = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.RESOLVED_CONVERSATIONS, start_date, end_date)
        active = total - resolved
        trends = await AnalyticsService._get_trend(db, workspace_id, AnalyticsMetricName.TOTAL_CONVERSATIONS, granularity=granularity)

        data = AnalyticsConversationsResponse(total=total, active=max(active, 0), resolved=resolved, trends=trends)
        return AnalyticsResponseEnvelope(data=data, freshness=freshness)

    @staticmethod
    async def get_sales(
        db: AsyncSession,
        workspace_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY,
    ) -> AnalyticsResponseEnvelope:
        freshness = await AnalyticsService._get_freshness(db, workspace_id)
        created = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.LEADS_CREATED, start_date, end_date)
        qualified = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.LEADS_QUALIFIED, start_date, end_date)
        trends = await AnalyticsService._get_trend(db, workspace_id, AnalyticsMetricName.LEADS_CREATED, granularity=granularity)

        data = AnalyticsSalesResponse(leads_created=created, leads_qualified=qualified, funnel_distribution={}, trends=trends)
        return AnalyticsResponseEnvelope(data=data, freshness=freshness)

    @staticmethod
    async def get_support(
        db: AsyncSession,
        workspace_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY,
    ) -> AnalyticsResponseEnvelope:
        freshness = await AnalyticsService._get_freshness(db, workspace_id)
        created = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.TICKETS_CREATED, start_date, end_date)
        resolved = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.TICKETS_RESOLVED, start_date, end_date)
        open_tickets = created - resolved
        trends = await AnalyticsService._get_trend(db, workspace_id, AnalyticsMetricName.TICKETS_CREATED, granularity=granularity)

        data = AnalyticsSupportResponse(tickets_created=created, tickets_resolved=resolved, open_tickets=max(open_tickets, 0), trends=trends)
        return AnalyticsResponseEnvelope(data=data, freshness=freshness)

    @staticmethod
    async def get_customer_care(
        db: AsyncSession,
        workspace_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY,
    ) -> AnalyticsResponseEnvelope:
        freshness = await AnalyticsService._get_freshness(db, workspace_id)
        complaints = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.COMPLAINTS, start_date, end_date)
        refunds = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.REFUNDS_REQUESTED, start_date, end_date)
        escalations = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.ESCALATIONS, start_date, end_date)
        trends = await AnalyticsService._get_trend(db, workspace_id, AnalyticsMetricName.COMPLAINTS, granularity=granularity)

        data = AnalyticsCustomerCareResponse(complaints=complaints, refunds_requested=refunds, escalations=escalations, trends=trends)
        return AnalyticsResponseEnvelope(data=data, freshness=freshness)

    @staticmethod
    async def get_handoffs(
        db: AsyncSession,
        workspace_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY,
    ) -> AnalyticsResponseEnvelope:
        freshness = await AnalyticsService._get_freshness(db, workspace_id)
        total = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.TOTAL_HANDOFFS, start_date, end_date)
        failed = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.FAILED_HANDOFFS, start_date, end_date)
        loops = await AnalyticsService._get_metric_total(db, workspace_id, AnalyticsMetricName.LOOP_PREVENTION_TRIGGERS, start_date, end_date)
        trends = await AnalyticsService._get_trend(db, workspace_id, AnalyticsMetricName.TOTAL_HANDOFFS, granularity=granularity)

        data = AnalyticsHandoffsResponse(total_handoffs=total, failed_handoffs=failed, loop_prevention_triggers=loops, trends=trends)
        return AnalyticsResponseEnvelope(data=data, freshness=freshness)

    @staticmethod
    async def get_trends(
        db: AsyncSession,
        workspace_id: UUID,
        metric_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY,
        days: int = DEFAULT_TREND_DAYS,
    ) -> AnalyticsResponseEnvelope:
        """Generic trend endpoint for any metric."""
        freshness = await AnalyticsService._get_freshness(db, workspace_id)
        try:
            metric = AnalyticsMetricName(metric_name)
        except ValueError:
            return AnalyticsResponseEnvelope(data={"error": f"Unknown metric: {metric_name}", "trends": []}, freshness=freshness)

        trends = await AnalyticsService._get_trend(db, workspace_id, metric, days=days, granularity=granularity)
        return AnalyticsResponseEnvelope(data={"metric": metric_name, "trends": trends}, freshness=freshness)
