"""
Phase 12: Central Metric Registry.

Single source of truth for all metric definitions. Every metric is defined
exactly once with its name, description, aggregation method, supported
dimensions, and the event types that feed it.

AnalyticsService, rollup generation, and dashboard APIs all consume this
registry — no duplicate metric definitions allowed.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.app.schemas.analytics import AnalyticsEventType, AnalyticsMetricName

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MetricDefinition:
    """Immutable definition of a single analytics metric."""
    metric_name: AnalyticsMetricName
    description: str
    aggregation: str  # "count" | "sum" | "avg"
    source_events: List[AnalyticsEventType]
    supported_dimensions: List[str] = field(default_factory=list)
    display_label: str = ""
    schema_version: int = 1


class _MetricRegistry:
    """
    Internal registry singleton. Populated at import time.
    Duplicate registration raises ValueError to prevent drift.
    """

    def __init__(self):
        self._metrics: Dict[AnalyticsMetricName, MetricDefinition] = {}

    def register(self, defn: MetricDefinition) -> None:
        if defn.metric_name in self._metrics:
            raise ValueError(
                f"Duplicate metric registration: {defn.metric_name.value}"
            )
        self._metrics[defn.metric_name] = defn

    def get(self, name) -> MetricDefinition:
        if isinstance(name, str):
            try:
                name = AnalyticsMetricName(name)
            except ValueError:
                raise KeyError(f"Metric not registered: {name}")
        defn = self._metrics.get(name)
        if defn is None:
            raise KeyError(f"Metric not registered: {name.value}")
        return defn

    def all_metrics(self) -> Dict[AnalyticsMetricName, MetricDefinition]:
        return dict(self._metrics)

    def events_for_metric(self, name: AnalyticsMetricName) -> List[AnalyticsEventType]:
        return self.get(name).source_events

    def metrics_for_event(self, event_type: AnalyticsEventType) -> List[MetricDefinition]:
        """Return every metric that should be updated when this event fires."""
        return [d for d in self._metrics.values() if event_type in d.source_events]


# ── Global singleton ─────────────────────────────────────
metric_registry = _MetricRegistry()

# ── Register all canonical metrics ────────────────────────
_DEFINITIONS = [
    MetricDefinition(
        metric_name=AnalyticsMetricName.TOTAL_CONVERSATIONS,
        description="Total conversations started",
        aggregation="count",
        source_events=[AnalyticsEventType.CONVERSATION_STARTED],
        display_label="Total Conversations",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.ACTIVE_CONVERSATIONS,
        description="Conversations currently active (started minus completed)",
        aggregation="count",
        source_events=[AnalyticsEventType.CONVERSATION_STARTED, AnalyticsEventType.CONVERSATION_COMPLETED],
        display_label="Active Conversations",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.RESOLVED_CONVERSATIONS,
        description="Conversations completed / resolved",
        aggregation="count",
        source_events=[AnalyticsEventType.CONVERSATION_COMPLETED],
        display_label="Resolved Conversations",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.MESSAGES_RECEIVED,
        description="Customer messages received",
        aggregation="count",
        source_events=[AnalyticsEventType.MESSAGE_RECEIVED],
        display_label="Messages Received",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.MESSAGES_SENT,
        description="Agent messages sent",
        aggregation="count",
        source_events=[AnalyticsEventType.MESSAGE_SENT],
        display_label="Messages Sent",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.LEADS_CREATED,
        description="Sales leads created",
        aggregation="count",
        source_events=[AnalyticsEventType.SALES_LEAD_CREATED],
        supported_dimensions=["source_agent"],
        display_label="Leads Created",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.LEADS_QUALIFIED,
        description="Sales leads that advanced past qualification",
        aggregation="count",
        source_events=[AnalyticsEventType.SALES_STAGE_CHANGED],
        supported_dimensions=["stage"],
        display_label="Leads Qualified",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.TICKETS_CREATED,
        description="Support tickets created",
        aggregation="count",
        source_events=[AnalyticsEventType.SUPPORT_TICKET_CREATED],
        display_label="Tickets Created",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.TICKETS_RESOLVED,
        description="Support tickets resolved",
        aggregation="count",
        source_events=[AnalyticsEventType.SUPPORT_TICKET_RESOLVED],
        display_label="Tickets Resolved",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.COMPLAINTS,
        description="Customer care complaints filed",
        aggregation="count",
        source_events=[AnalyticsEventType.CUSTOMER_CARE_CASE_CREATED],
        display_label="Complaints",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.REFUNDS_REQUESTED,
        description="Refund requests",
        aggregation="count",
        source_events=[AnalyticsEventType.CUSTOMER_CARE_CASE_CREATED],
        supported_dimensions=["refund_requested"],
        display_label="Refunds Requested",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.ESCALATIONS,
        description="Cases escalated to human agents",
        aggregation="count",
        source_events=[AnalyticsEventType.HUMAN_ESCALATION],
        display_label="Escalations",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.TOTAL_HANDOFFS,
        description="Total agent-to-agent handoffs",
        aggregation="count",
        source_events=[AnalyticsEventType.HANDOFF_COMPLETED],
        supported_dimensions=["from_agent", "to_agent"],
        display_label="Total Handoffs",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.FAILED_HANDOFFS,
        description="Handoffs that failed",
        aggregation="count",
        source_events=[AnalyticsEventType.HANDOFF_FAILED],
        display_label="Failed Handoffs",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.LOOP_PREVENTION_TRIGGERS,
        description="Times loop prevention was triggered",
        aggregation="count",
        source_events=[AnalyticsEventType.HUMAN_ESCALATION],
        supported_dimensions=["reason"],
        display_label="Loop Prevention Triggers",
    ),
    MetricDefinition(
        metric_name=AnalyticsMetricName.HUMAN_ESCALATIONS,
        description="Total human escalations across all agents",
        aggregation="count",
        source_events=[AnalyticsEventType.HUMAN_ESCALATION],
        display_label="Human Escalations",
    ),
]

for _defn in _DEFINITIONS:
    metric_registry.register(_defn)
