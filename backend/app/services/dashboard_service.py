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
        """
        # 1. Total Conversations
        total_conv_query = select(func.count(Conversation.id)).where(
            Conversation.workspace_id == workspace_id
        )
        total_conversations = await db.scalar(total_conv_query) or 0

        # Postgres count returns integers, but sum with case requires careful handling
        # Let's use individual queries for safety and clarity

        # Total tickets
        total_tickets_query = select(func.count(Ticket.id)).where(
            Ticket.workspace_id == workspace_id
        )
        total_tickets = await db.scalar(total_tickets_query) or 0

        # Resolved/Closed tickets
        resolved_tickets_query = select(func.count(Ticket.id)).where(
            Ticket.workspace_id == workspace_id,
            Ticket.status.in_(["resolved", "closed"]),
        )
        resolved_tickets = await db.scalar(resolved_tickets_query) or 0

        # Open tickets
        open_tickets_query = select(func.count(Ticket.id)).where(
            Ticket.workspace_id == workspace_id,
            Ticket.status.in_(["open", "in_progress"]),
        )
        open_tickets = await db.scalar(open_tickets_query) or 0

        resolution_rate = (
            round((resolved_tickets / total_tickets * 100), 1)
            if total_tickets > 0
            else 0.0
        )

        # 3. Lead Conversion (Percentage of handoffs to 'sales' over total conversations)
        # We proxy this by counting distinct conversations that had a handoff to 'sales'
        sales_handoffs_query = (
            select(func.count(func.distinct(Handoff.conversation_id)))
            .join(Conversation, Handoff.conversation_id == Conversation.id)
            .where(
                Conversation.workspace_id == workspace_id, Handoff.to_agent == "sales"
            )
        )
        sales_handoffs = await db.scalar(sales_handoffs_query) or 0

        lead_conversion = (
            round((sales_handoffs / total_conversations * 100), 1)
            if total_conversations > 0
            else 0.0
        )

        # 4. Recent Activity (Last 5 conversations)
        recent_activity_query = (
            select(Conversation)
            .where(Conversation.workspace_id == workspace_id)
            .order_by(Conversation.updated_at.desc())
            .limit(5)
        )

        result = await db.execute(recent_activity_query)
        recent_conversations = result.scalars().all()

        recent_activity = []
        for conv in recent_conversations:
            recent_activity.append(
                {
                    "id": str(conv.id),
                    "channel": conv.channel,
                    "status": conv.status,
                    "updated_at": conv.updated_at.isoformat(),
                }
            )

        # 5. Sentiment Distribution
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

        # 6. Top Topics
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

        # 7. Chart Data (Conversations over the last 7 days)
        chart_data = []
        now = datetime.now(timezone.utc)
        for i in range(6, -1, -1):
            target_date = (now - timedelta(days=i)).date()
            day_start = datetime.combine(target_date, datetime.min.time()).replace(
                tzinfo=timezone.utc
            )
            day_end = datetime.combine(target_date, datetime.max.time()).replace(
                tzinfo=timezone.utc
            )

            day_query = select(func.count(Conversation.id)).where(
                Conversation.workspace_id == workspace_id,
                Conversation.created_at >= day_start,
                Conversation.created_at <= day_end,
            )
            count = await db.scalar(day_query) or 0

            chart_data.append(
                {"date": target_date.strftime("%b %d"), "conversations": count}
            )

        return {
            "kpis": {
                "total_conversations": total_conversations,
                "resolution_rate": resolution_rate,
                "lead_conversion": lead_conversion,
                "open_tickets": open_tickets,
            },
            "chart_data": chart_data,
            "recent_activity": recent_activity,
            "sentiment_distribution": sentiment_distribution,
            "top_topics": top_topics,
        }
