import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, desc

from backend.app.models.analytics import AnalyticsDailyRollup
from backend.app.models.intel_rollups import IntelDailyTopicRollup, IntelDailySentimentRollup
from backend.app.models.workspace import Workspace
from backend.app.models.business_analyst import BusinessInsight, InsightLineage
from backend.app.core.telemetry import log_business_telemetry
from backend.app.core.config import settings

ENGINE_VERSION = "1.0.0"
CONFIG_VERSION = "1.0.0"

class RollupStaleError(Exception):
    pass

class InsightEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_fingerprint(self, workspace_id: str, category: str, date_range: str, insight_type: str) -> str:
        """Deterministic fingerprint for insight deduplication."""
        base = f"{workspace_id}:{category}:{date_range}:{insight_type}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    async def _validate_freshness(self, workspace_id: str) -> Tuple[datetime, uuid.UUID]:
        """Validates that rollups have been refreshed recently."""
        # Check AnalyticsDailyRollup freshness
        stmt = select(func.max(AnalyticsDailyRollup.updated_at)).where(
            AnalyticsDailyRollup.workspace_id == workspace_id
        )
        res1 = await self.db.execute(stmt)
        latest_analytics = res1.scalar()

        # Check IntelDailyTopicRollup freshness
        stmt_intel = select(func.max(IntelDailyTopicRollup.updated_at)).where(
            IntelDailyTopicRollup.workspace_id == workspace_id
        )
        res2 = await self.db.execute(stmt_intel)
        latest_intel = res2.scalar()

        # If no data exists, we consider it "fresh" enough to generate nothing, or we can just use now
        freshness_ts = datetime.now(timezone.utc)
        if latest_analytics and latest_intel:
            freshness_ts = min(latest_analytics, latest_intel)
            
            # If older than configured threshold (default 48 hours), mark as stale
            max_stale_hours = getattr(settings, "BUSINESS_ANALYST_MAX_STALE_HOURS", 48)
            if datetime.now(timezone.utc) - freshness_ts > timedelta(hours=max_stale_hours):
                log_business_telemetry(
                    "stale_rollup_detected", 
                    workspace_id=workspace_id,
                    details={"latest_analytics": latest_analytics.isoformat(), "latest_intel": latest_intel.isoformat()}
                )
                raise RollupStaleError("Rollups are stale. Insight generation aborted.")
            
        snapshot_id = uuid.uuid4()
        return freshness_ts, snapshot_id

    def _calculate_confidence(self, sample_size: int, trend_strength: float, historical_variance: float) -> Tuple[float, str]:
        """
        Explicit formula calculating confidence score based on deterministic inputs.
        """
        confidence = 50.0  # Base confidence
        reason = []

        # Sample size modifier
        if sample_size > 1000:
            confidence += 20
            reason.append("High sample size (+20)")
        elif sample_size > 100:
            confidence += 10
            reason.append("Moderate sample size (+10)")
        else:
            confidence -= 10
            reason.append("Low sample size (-10)")

        # Trend strength modifier
        if abs(trend_strength) > 0.5:
            confidence += 15
            reason.append("Strong trend signal (+15)")
        elif abs(trend_strength) > 0.2:
            confidence += 5
            reason.append("Moderate trend signal (+5)")
            
        # Variance penalty
        if historical_variance > 0.8:
            confidence -= 15
            reason.append("High historical variance (-15)")
            
        # Cap
        confidence = min(max(confidence, 0.0), 99.9)
        return confidence, ", ".join(reason)

    async def _detect_analytics_trends(self, workspace_id: str, snapshot_id: uuid.UUID, freshness_ts: datetime, current_start: datetime, current_end: datetime, prev_start: datetime, prev_end: datetime) -> List[BusinessInsight]:
        insights = []
        
        # Get metrics for current window
        stmt_curr = select(
            AnalyticsDailyRollup.metric_name, 
            func.sum(AnalyticsDailyRollup.value).label('total')
        ).where(
            AnalyticsDailyRollup.workspace_id == workspace_id,
            AnalyticsDailyRollup.time_bucket >= current_start,
            AnalyticsDailyRollup.time_bucket < current_end
        ).group_by(AnalyticsDailyRollup.metric_name)
        
        res_curr = await self.db.execute(stmt_curr)
        curr_metrics = {row.metric_name: row.total for row in res_curr.all()}
        
        # Get metrics for previous window
        stmt_prev = select(
            AnalyticsDailyRollup.metric_name, 
            func.sum(AnalyticsDailyRollup.value).label('total')
        ).where(
            AnalyticsDailyRollup.workspace_id == workspace_id,
            AnalyticsDailyRollup.time_bucket >= prev_start,
            AnalyticsDailyRollup.time_bucket < prev_end
        ).group_by(AnalyticsDailyRollup.metric_name)
        
        res_prev = await self.db.execute(stmt_prev)
        prev_metrics = {row.metric_name: row.total for row in res_prev.all()}
        
        date_range_str = f"{current_start.date()}_to_{current_end.date()}"
        
        for metric, curr_val in curr_metrics.items():
            prev_val = prev_metrics.get(metric, 0)
            if prev_val == 0 and curr_val > 0:
                trend_strength = 1.0 # 100% increase
            elif prev_val == 0 and curr_val == 0:
                continue
            else:
                trend_strength = float((curr_val - prev_val) / prev_val)
                
            # Only generate insight if there's a significant change (> 15%)
            if abs(trend_strength) > 0.15:
                direction = "increased" if trend_strength > 0 else "decreased"
                percent_change = abs(trend_strength) * 100
                
                sample_size = int(curr_val + prev_val) # Proxy for sample size
                conf, reason = self._calculate_confidence(sample_size, trend_strength, 0.2)
                
                fingerprint = self._generate_fingerprint(workspace_id, "analytics_trend", date_range_str, metric)
                
                # Check for existing
                existing_res = await self.db.execute(select(BusinessInsight).where(BusinessInsight.fingerprint == fingerprint, BusinessInsight.workspace_id == workspace_id))
                if existing_res.scalar():
                    log_business_telemetry("duplicate_insight_prevented", workspace_id=workspace_id, details={"fingerprint": fingerprint})
                    continue

                priority = "medium"
                if abs(trend_strength) > 0.5:
                    priority = "high"
                
                insight = BusinessInsight(
                    workspace_id=workspace_id,
                    title=f"{metric} {direction} by {percent_change:.1f}%",
                    description=f"The metric '{metric}' {direction} from {prev_val} to {curr_val} over the last window.",
                    category="analytics_trend",
                    confidence=conf,
                    confidence_reason=reason,
                    priority=priority,
                    evidence_snapshot={
                        "metric_name": metric,
                        "current_value": float(curr_val),
                        "previous_value": float(prev_val),
                        "percent_change": float(percent_change),
                        "date_range": date_range_str
                    },
                    insight_version=1,
                    generated_by_engine_version=ENGINE_VERSION,
                    engine_config_version=CONFIG_VERSION,
                    data_freshness_timestamp=freshness_ts,
                    snapshot_id=snapshot_id,
                    fingerprint=fingerprint
                )
                self.db.add(insight)
                await self.db.flush() # Get insight ID
                
                # Add lineage
                lineage = InsightLineage(
                    insight_id=insight.id,
                    source_type="AnalyticsDailyRollup",
                    source_identifier=metric,
                    source_date_range={"start": current_start.isoformat(), "end": current_end.isoformat()}
                )
                self.db.add(lineage)
                insights.append(insight)
                
        return insights

    async def generate_insights(self, workspace_id: str, lookback_days: int = 7) -> List[BusinessInsight]:
        """
        Main entrypoint for generating insights.
        """
        try:
            snapshot_ts, snapshot_id = await self._validate_freshness(workspace_id)
        except RollupStaleError:
            return []

        # Use exactly the snapshot timestamp as the atomic current_end
        current_end = snapshot_ts
        current_start = current_end - timedelta(days=lookback_days)
        
        prev_end = current_start
        prev_start = prev_end - timedelta(days=lookback_days)

        insights = []
        new_insights = await self._detect_analytics_trends(workspace_id, snapshot_id, snapshot_ts, current_start, current_end, prev_start, prev_end)
        insights.extend(new_insights)

        # Sort and apply workspace limits (e.g. max 50 top insights)
        insights.sort(key=lambda x: (x.priority == 'critical', x.priority == 'high', x.confidence), reverse=True)
        top_insights = insights[:50]
        
        # Safely archive insights that didn't make the cut instead of destructive deletion
        for ins in insights[50:]:
            ins.status = "superseded"
            
        await self.db.commit()
        
        log_business_telemetry(
            "insights_generated", 
            workspace_id=workspace_id, 
            details={"count": len(top_insights)}
        )
        return top_insights
