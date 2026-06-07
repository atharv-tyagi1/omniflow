import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.app.models.business_analyst import BusinessInsight, ExecutiveReport, BusinessRecommendation, BusinessQuestionAudit
from backend.app.core.telemetry import log_business_telemetry
from backend.app.models.workspace import Workspace

ENGINE_VERSION = "1.0.0"
CONFIG_VERSION = "1.0.0"

class ExecutiveSummaryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_fingerprint(self, workspace_id: str, report_type: str, report_period: str) -> str:
        base = f"{workspace_id}:{report_type}:{report_period}:{ENGINE_VERSION}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def _detect_conflicts(self, insights: List[BusinessInsight]) -> List[dict]:
        """Read-only conflict detection pass."""
        conflicts = []
        # Basic heuristic for demonstration: flag if both increase and decrease of same metric
        # Real implementation would have a conflict rule matrix
        metrics_seen = {}
        for insight in insights:
            ev = insight.evidence_snapshot
            if not ev or "metric_name" not in ev:
                continue
                
            metric = ev["metric_name"]
            direction = "increased" if "increased" in insight.title else "decreased"
            
            if metric in metrics_seen and metrics_seen[metric] != direction:
                conflicts.append({
                    "metric": metric,
                    "insight_1": str(insight.id),
                    "issue": f"Contradictory trends detected for {metric}"
                })
                log_business_telemetry("insight_conflict_detected", workspace_id=str(insight.workspace_id), details={"metric": metric})
            else:
                metrics_seen[metric] = direction
                
        return conflicts

    async def generate_report(self, workspace_id: str, report_type: str, report_period: str) -> Optional[ExecutiveReport]:
        try:
            fingerprint = self._generate_fingerprint(workspace_id, report_type, report_period)
            
            # Idempotency check
            existing_res = await self.db.execute(select(ExecutiveReport).where(ExecutiveReport.fingerprint == fingerprint))
            existing = existing_res.scalar()
            if existing:
                log_business_telemetry("duplicate_report_prevented", workspace_id=workspace_id, details={"fingerprint": fingerprint})
                return existing

            now = datetime.now(timezone.utc)
            
            # Fetch recent insights for the period
            # Simplified: fetch top active insights
            stmt = select(BusinessInsight).where(
                BusinessInsight.workspace_id == workspace_id,
                BusinessInsight.status == "active"
            ).order_by(BusinessInsight.created_at.desc()).limit(20)
            
            res_insights = await self.db.execute(stmt)
            insights = res_insights.scalars().all()
            if not insights:
                return None # No data to report
                
            conflicts = self._detect_conflicts(insights)
            
            # Assume snapshot_id and freshness are inherited from the most recent insight
            latest_insight = insights[0]
            
            summary = {
                "overview": f"Executive summary for {report_period}",
                "insight_count": len(insights),
                "key_insights": [{"id": str(i.id), "title": i.title, "priority": i.priority} for i in insights[:5]],
                "conflicts_detected": conflicts
            }

            report = ExecutiveReport(
                workspace_id=workspace_id,
                report_type=report_type,
                report_period=report_period,
                summary=summary,
                report_version=1,
                generated_by_engine_version=ENGINE_VERSION,
                engine_config_version=CONFIG_VERSION,
                data_freshness_timestamp=latest_insight.data_freshness_timestamp,
                snapshot_id=latest_insight.snapshot_id,
                fingerprint=fingerprint
            )
            self.db.add(report)
            await self.db.commit()
            
            log_business_telemetry(
                "reports_generated", 
                workspace_id=workspace_id, 
                details={"report_type": report_type, "report_period": report_period}
            )
            
            return report
            
        except Exception as e:
            log_business_telemetry(
                "report_generation_failure",
                workspace_id=workspace_id,
                details={"report_type": report_type, "report_period": report_period, "error": str(e)}
            )
            raise

    async def cleanup_old_reports(self, workspace_id: str, retention_days: int = 90):
        """Workspace-level retention controls."""
        import time
        start_time = time.time()
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        stmt = delete(ExecutiveReport).where(
            ExecutiveReport.workspace_id == workspace_id,
            ExecutiveReport.generated_at < cutoff
        )
        report_res = await self.db.execute(stmt)
        report_count = report_res.rowcount
        
        # Also cleanup old BusinessQuestionAudits
        audit_stmt = delete(BusinessQuestionAudit).where(
            BusinessQuestionAudit.workspace_id == workspace_id,
            BusinessQuestionAudit.created_at < cutoff
        )
        audit_res = await self.db.execute(audit_stmt)
        audit_count = audit_res.rowcount
        
        await self.db.commit()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        log_business_telemetry(
            "cleanup_executed",
            workspace_id=workspace_id,
            details={
                "report_cleanup_count": report_count,
                "audit_cleanup_count": audit_count,
                "duration_ms": duration_ms
            }
        )
