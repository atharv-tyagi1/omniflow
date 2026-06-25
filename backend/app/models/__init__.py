"""OmniFlow database models package — exports all SQLAlchemy models."""

from backend.app.models.base import Base, TimestampMixin

# Core tenant models
from backend.app.models.workspace import Workspace
from backend.app.models.user import User
from backend.app.models.workspace_member import WorkspaceMember

# Customer & Conversation models
from backend.app.models.customer import Customer
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.handoff import Handoff
from backend.app.models.lead_profile import LeadProfile

# Knowledge Base models
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk

# Support & Customer Care models
from backend.app.models.ticket import Ticket
from backend.app.models.customer_care_case import CustomerCareCase
from backend.app.models.sentiment import Sentiment
from backend.app.models.topic import Topic

# Analytics models
from backend.app.models.analytics_report import AnalyticsReport
from backend.app.models.router_event import RouterEvent
from backend.app.models.dataset import Dataset
from backend.app.models.dataset_query import DatasetQuery

# Phase 12: Analytics Foundation
from backend.app.models.analytics import (
    AnalyticsOutbox,
    AnalyticsEvent,
    AnalyticsHourlyRollup,
    AnalyticsDailyRollup,
)

# Workflow models
from backend.app.models.workflow import Workflow
from backend.app.models.workflow_version import WorkflowVersion
from backend.app.models.workflow_node import WorkflowNode
from backend.app.models.workflow_edge import WorkflowEdge
from backend.app.models.workflow_run import WorkflowRun
from backend.app.models.workflow_run_step import WorkflowRunStep
from backend.app.models.workflow_log import WorkflowLog
from backend.app.models.workflow_event_queue import WorkflowEventQueue
from backend.app.models.workflow_dead_letter_event import WorkflowDeadLetterEvent
from backend.app.models.agent import Agent

# Communication models
from backend.app.models.voice_interaction import VoiceInteraction

# System models
from backend.app.models.notification import Notification
from backend.app.models.audit_log import AuditLog

# Phase 13: Conversation Intel Models
from backend.app.models.intel import (
    TopicRegistry,
    ConversationIntelligence,
    ConversationIntent,
    ConversationTopic,
    ConversationSentiment,
    ConversationResolution,
    ConversationSummary,
)
from backend.app.models.intel_rollups import (
    IntelDailyTopicRollup,
    IntelDailyIntentRollup,
    IntelDailySentimentRollup,
    IntelDailyResolutionRollup,
)

# Phase 13.5: Public API Models
from backend.app.models.public_api import (
    PublicApiKey,
    PublicApiKeyScope,
    PublicApiKeyRotation,
    IdempotencyKey,
    PublicWebhook,
    PublicAsyncJob,
)

# Phase 14: Business Analyst Engine Models
from backend.app.models.business_analyst import (
    BusinessInsight,
    BusinessRecommendation,
    ExecutiveReport,
    InsightLineage,
    BusinessQuestionAudit,
)

# Phase 21.2C: Agent Platform Models
from backend.app.models.agent_template import AgentTemplate
from backend.app.models.agent_version import AgentVersion
from backend.app.models.agent_model import AgentModel
from backend.app.models.agent_prompt import AgentPrompt
from backend.app.models.agent_tool_policy import AgentToolPolicy
from backend.app.models.channel import Channel
from backend.app.models.agent_channel import AgentChannel
from backend.app.models.conversation_participant import ConversationParticipant
from backend.app.models.workspace_memory import WorkspaceMemory
from backend.app.models.agent_memory import AgentMemory
from backend.app.models.conversation_memory import ConversationMemory
from backend.app.models.agent_run import AgentRun
from backend.app.models.agent_run_step import AgentRunStep
from backend.app.models.agent_decision_trace import AgentDecisionTrace
from backend.app.models.agent_log import AgentLog
from backend.app.models.agent_metric import AgentMetric
from backend.app.models.agent_permission import AgentPermission


__all__ = [
    "Base",
    "TimestampMixin",
    "Workspace",
    "WorkspaceMember",
    "User",
    "Customer",
    "Conversation",
    "Message",
    "Handoff",
    "LeadProfile",
    "Document",
    "DocumentChunk",
    "Ticket",
    "CustomerCareCase",
    "Sentiment",
    "Topic",
    "AnalyticsReport",
    "RouterEvent",
    "Dataset",
    "DatasetQuery",
    "Workflow",
    "WorkflowRun",
    "WorkflowVersion",
    "WorkflowNode",
    "WorkflowEdge",
    "WorkflowRunStep",
    "WorkflowLog",
    "WorkflowEventQueue",
    "WorkflowDeadLetterEvent",
    "Agent",
    "VoiceInteraction",
    "Notification",
    "AuditLog",
    "TopicRegistry",
    "ConversationIntelligence",
    "ConversationIntent",
    "ConversationTopic",
    "ConversationSentiment",
    "ConversationResolution",
    "ConversationSummary",
    "IntelDailyTopicRollup",
    "IntelDailyIntentRollup",
    "IntelDailySentimentRollup",
    "IntelDailyResolutionRollup",
    "PublicApiKey",
    "PublicApiKeyScope",
    "PublicApiKeyRotation",
    "IdempotencyKey",
    "PublicWebhook",
    "PublicAsyncJob",
    "BusinessInsight",
    "BusinessRecommendation",
    "ExecutiveReport",
    "InsightLineage",
    "BusinessQuestionAudit",
    "AgentTemplate",
    "AgentVersion",
    "AgentModel",
    "AgentPrompt",
    "AgentToolPolicy",
    "Channel",
    "AgentChannel",
    "ConversationParticipant",
    "WorkspaceMemory",
    "AgentMemory",
    "ConversationMemory",
    "AgentRun",
    "AgentRunStep",
    "AgentDecisionTrace",
    "AgentLog",
    "AgentMetric",
    "AgentPermission",
]
