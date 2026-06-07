"""
Phase 12: Analytics schemas, enums, and response models.
Strict types for event_type and metric_name. UTC-aware timestamps.
Standardized API response envelope with freshness metadata.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime, timezone
from uuid import UUID


# ──────────────────────────────────────────────────────────
# Strict Enums
# ──────────────────────────────────────────────────────────

class AnalyticsEventType(str, Enum):
    """Strict enum for all analytics event types. No free-form strings allowed."""
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_COMPLETED = "conversation_completed"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    HANDOFF_CREATED = "handoff_created"
    HANDOFF_COMPLETED = "handoff_completed"
    HANDOFF_FAILED = "handoff_failed"
    HUMAN_ESCALATION = "human_escalation"
    SALES_LEAD_CREATED = "sales_lead_created"
    SALES_STAGE_CHANGED = "sales_stage_changed"
    SUPPORT_TICKET_CREATED = "support_ticket_created"
    SUPPORT_TICKET_RESOLVED = "support_ticket_resolved"
    CUSTOMER_CARE_CASE_CREATED = "customer_care_case_created"
    CUSTOMER_CARE_CASE_CLOSED = "customer_care_case_closed"
    CONVERSATION_INTEL_PENDING = "conversation_intel_pending"


class AnalyticsMetricName(str, Enum):
    """Strict enum for rollup metric names. Centrally defined, versioned."""
    TOTAL_CONVERSATIONS = "total_conversations"
    ACTIVE_CONVERSATIONS = "active_conversations"
    RESOLVED_CONVERSATIONS = "resolved_conversations"
    MESSAGES_RECEIVED = "messages_received"
    MESSAGES_SENT = "messages_sent"
    LEADS_CREATED = "leads_created"
    LEADS_QUALIFIED = "leads_qualified"
    TICKETS_CREATED = "tickets_created"
    TICKETS_RESOLVED = "tickets_resolved"
    COMPLAINTS = "complaints"
    REFUNDS_REQUESTED = "refunds_requested"
    ESCALATIONS = "escalations"
    TOTAL_HANDOFFS = "total_handoffs"
    FAILED_HANDOFFS = "failed_handoffs"
    LOOP_PREVENTION_TRIGGERS = "loop_prevention_triggers"
    HUMAN_ESCALATIONS = "human_escalations"


class AnalyticsGranularity(str, Enum):
    """Granularity for trend queries."""
    HOURLY = "hourly"
    DAILY = "daily"


# ──────────────────────────────────────────────────────────
# Request / Filter Schemas
# ──────────────────────────────────────────────────────────

class AnalyticsDateRange(BaseModel):
    """Shared date range filter. All dates normalized to UTC."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    granularity: AnalyticsGranularity = AnalyticsGranularity.DAILY

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def ensure_utc(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class AnalyticsEventCreate(BaseModel):
    """Payload for creating an analytics event (internal use)."""
    workspace_id: UUID
    conversation_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    event_type: AnalyticsEventType
    source_agent: Optional[str] = None
    target_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    schema_version: int = 1

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────

class AnalyticsFreshness(BaseModel):
    """Freshness metadata included in every analytics response."""
    as_of: datetime
    last_ingested_at: Optional[datetime] = None
    rollup_lag_seconds: int = 0


class AnalyticsResponseEnvelope(BaseModel):
    """Standard response envelope for all analytics endpoints."""
    data: Any
    freshness: AnalyticsFreshness


class KPI(BaseModel):
    label: str
    value: int | float
    trend: Optional[float] = None  # percentage change vs previous period


class ChartDataPoint(BaseModel):
    date: str
    value: int | float


class AnalyticsOverviewResponse(BaseModel):
    kpis: Dict[str, KPI]
    trends: List[ChartDataPoint]


class AnalyticsConversationsResponse(BaseModel):
    total: int
    active: int
    resolved: int
    trends: List[ChartDataPoint]


class AnalyticsSalesResponse(BaseModel):
    leads_created: int
    leads_qualified: int
    funnel_distribution: Dict[str, int]
    trends: List[ChartDataPoint]


class AnalyticsSupportResponse(BaseModel):
    tickets_created: int
    tickets_resolved: int
    open_tickets: int
    trends: List[ChartDataPoint]


class AnalyticsCustomerCareResponse(BaseModel):
    complaints: int
    refunds_requested: int
    escalations: int
    trends: List[ChartDataPoint]


class AnalyticsHandoffsResponse(BaseModel):
    total_handoffs: int
    failed_handoffs: int
    loop_prevention_triggers: int
    trends: List[ChartDataPoint]
