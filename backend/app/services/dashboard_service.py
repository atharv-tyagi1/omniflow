from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone

from backend.app.models.conversation import Conversation
from backend.app.models.ticket import Ticket
from backend.app.models.handoff import Handoff


class DashboardService:
    @staticmethod
    async def get_dashboard_metrics(db: AsyncSession, workspace_id: UUID) -> dict:
        """
        Aggregate operational metrics for the dashboard.
        Phase 12: Thin adapter over AnalyticsService (single source of truth).
        """
        from backend.app.services.analytics.service import AnalyticsService

        # 1. Fetch from single source of truth
        overview = await AnalyticsService.get_overview(db, workspace_id)
        support = await AnalyticsService.get_support(db, workspace_id)
        sales = await AnalyticsService.get_sales(db, workspace_id)

        # 2. Map to legacy dashboard format
        total_conv = overview.data.kpis["total_conversations"].value
        total_tickets = support.data.tickets_created
        resolved_tickets = support.data.tickets_resolved
        open_tickets = support.data.open_tickets

        resolution_rate = (
            round((resolved_tickets / total_tickets * 100), 1)
            if total_tickets > 0 else 0.0
        )

        sales_handoffs = sales.data.leads_created  # proxy for lead conversion
        lead_conversion = (
            round((sales_handoffs / total_conv * 100), 1)
            if total_conv > 0 else 0.0
        )

        chart_data = [
            # format "YYYY-MM-DD" to "MMM DD"
            {
                "date": datetime.strptime(point.date, "%Y-%m-%d").strftime("%b %d"),
                "conversations": point.value
            }
            for point in overview.data.trends
        ]

        # 3. Recent Activity (Last 5 conversations)
        recent_activity_query = (
            select(Conversation)
            .where(Conversation.workspace_id == workspace_id)
            .order_by(Conversation.updated_at.desc())
            .limit(5)
        )
        result = await db.execute(recent_activity_query)
        recent_conversations = result.scalars().all()

        recent_activity = [
            {
                "id": str(conv.id),
                "channel": conv.channel,
                "status": conv.status,
                "updated_at": conv.updated_at.isoformat(),
            }
            for conv in recent_conversations
        ]

        # 4. Sentiment Distribution (raw query for now until dimensional rollups added)
        from backend.app.models.sentiment import Sentiment
        from backend.app.models.topic import Topic

        sentiment_query = (
            select(Sentiment.label, func.count(Sentiment.id))
            .join(Conversation, Sentiment.conversation_id == Conversation.id)
            .where(Conversation.workspace_id == workspace_id)
            .group_by(Sentiment.label)
        )
        sentiment_result = await db.execute(sentiment_query)
        sentiment_distribution = [
            {"name": row[0].capitalize(), "value": row[1]}
            for row in sentiment_result.all()
        ]

        # 5. Top Topics (raw query for now)
        topics_query = (
            select(Topic.topic_name, func.count(Topic.id))
            .join(Conversation, Topic.conversation_id == Conversation.id)
            .where(Conversation.workspace_id == workspace_id)
            .group_by(Topic.topic_name)
            .order_by(func.count(Topic.id).desc())
            .limit(5)
        )
        topics_result = await db.execute(topics_query)
        top_topics = [{"name": row[0], "count": row[1]} for row in topics_result.all()]

        return {
            "kpis": {
                "total_conversations": total_conv,
                "resolution_rate": resolution_rate,
                "lead_conversion": lead_conversion,
                "open_tickets": open_tickets,
            },
            "chart_data": chart_data,
            "recent_activity": recent_activity,
            "sentiment_distribution": sentiment_distribution,
            "top_topics": top_topics,
        }
