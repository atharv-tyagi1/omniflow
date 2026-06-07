"""Phase 13: Conversation Intelligence API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.response import SuccessResponse
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.models.user import User
from backend.app.models.intel import ConversationIntelligence
from backend.app.models.intel_rollups import (
    IntelDailyTopicRollup,
    IntelDailyIntentRollup,
    IntelDailySentimentRollup,
    IntelDailyResolutionRollup
)
from backend.app.services.intel.rebuild_service import IntelRebuildService

router = APIRouter(prefix="/intel", tags=["Intelligence"])

class RebuildRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    force_reanalyze: bool = False

@router.post("/rebuild", response_model=SuccessResponse)
async def trigger_intel_rebuild(
    data: RebuildRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Trigger an asynchronous rebuild of conversation intelligence."""
    try:
        queued = await IntelRebuildService.rebuild_workspace(
            db=db,
            workspace_id=workspace_id,
            start_date=data.start_date,
            end_date=data.end_date,
            force_reanalyze=data.force_reanalyze
        )
        return SuccessResponse(
            data={"conversations_queued": queued},
            message=f"Queued {queued} conversations for intelligence extraction."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics/trending", response_model=SuccessResponse)
async def get_trending_topics(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Get the most common topics over the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(IntelDailyTopicRollup.topic_name, func.sum(IntelDailyTopicRollup.value).label("count"))
        .where(
            IntelDailyTopicRollup.workspace_id == workspace_id,
            IntelDailyTopicRollup.time_bucket >= cutoff
        )
        .group_by(IntelDailyTopicRollup.topic_name)
        .order_by(desc("count"))
        .limit(10)
    )
    result = await db.execute(stmt)
    data = [{"topic": row.topic_name, "count": float(row.count)} for row in result.all()]
    
    return SuccessResponse(data={"trending_topics": data})


@router.get("/intents/distribution", response_model=SuccessResponse)
async def get_intent_distribution(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Get the distribution of primary intents over the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(IntelDailyIntentRollup.intent_name, func.sum(IntelDailyIntentRollup.value).label("count"))
        .where(
            IntelDailyIntentRollup.workspace_id == workspace_id,
            IntelDailyIntentRollup.time_bucket >= cutoff
        )
        .group_by(IntelDailyIntentRollup.intent_name)
        .order_by(desc("count"))
    )
    result = await db.execute(stmt)
    data = [{"intent": row.intent_name, "count": float(row.count)} for row in result.all()]
    
    return SuccessResponse(data={"intent_distribution": data})


@router.get("/sentiment/trend", response_model=SuccessResponse)
async def get_sentiment_trend(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Get the trend of sentiments over the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(
            IntelDailySentimentRollup.time_bucket,
            IntelDailySentimentRollup.sentiment,
            func.sum(IntelDailySentimentRollup.value).label("count")
        )
        .where(
            IntelDailySentimentRollup.workspace_id == workspace_id,
            IntelDailySentimentRollup.time_bucket >= cutoff
        )
        .group_by(IntelDailySentimentRollup.time_bucket, IntelDailySentimentRollup.sentiment)
        .order_by(IntelDailySentimentRollup.time_bucket.asc())
    )
    result = await db.execute(stmt)
    
    # Restructure for charting
    trends = {}
    for row in result.all():
        date_str = row.time_bucket.strftime("%Y-%m-%d")
        if date_str not in trends:
            trends[date_str] = {}
        trends[date_str][row.sentiment] = float(row.count)
        
    return SuccessResponse(data={"sentiment_trend": trends})


@router.get("/conversation/{conversation_id}", response_model=SuccessResponse)
async def get_conversation_intel(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace_id: UUID = Depends(get_current_workspace_id),
):
    """Get intelligence for a specific conversation."""
    stmt = (
        select(ConversationIntelligence)
        .where(
            ConversationIntelligence.workspace_id == workspace_id,
            ConversationIntelligence.conversation_id == conversation_id
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    intel = result.scalar_one_or_none()
    
    if not intel:
        raise HTTPException(status_code=404, detail="Intelligence not found or pending.")
        
    return SuccessResponse(
        data={
            "intel": {
                "primary_intent": intel.primary_intent,
                "sentiment": intel.sentiment,
                "resolution": intel.resolution,
                "needs_review": intel.needs_review,
                "confidence": float(intel.raw_confidence),
                "review_reason": intel.review_reason,
            }
        }
    )
