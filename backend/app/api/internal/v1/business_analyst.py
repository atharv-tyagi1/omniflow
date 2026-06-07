from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional, Any

from backend.app.core.database import get_db
from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.models.user import User
from backend.app.services.ai_service import AIService
from backend.app.services.business.insight_engine import InsightEngine
from backend.app.services.business.business_analyst_service import BusinessAnalystService
from backend.app.core.telemetry import log_business_telemetry

router = APIRouter()

class BusinessQuestionRequest(BaseModel):
    workspace_id: UUID
    question: str = Field(..., max_length=500)

class BusinessQuestionResponse(BaseModel):
    answer: str
    insights_used: List[str]

@router.post("/questions", response_model=BusinessQuestionResponse, status_code=status.HTTP_200_OK)
async def ask_business_question(
    request: BusinessQuestionRequest,
    db: AsyncSession = Depends(get_db),
    auth_workspace_id: UUID = Depends(get_current_workspace_id),
    current_user: User = Depends(get_current_user)
):
    """
    Ask the Business Analyst a deterministic business question based on the existing rollups.
    """
    try:
        ai_service = AIService()
        insight_engine = InsightEngine(db)
        analyst_service = BusinessAnalystService(db=db, insight_engine=insight_engine)
        
        # Explicitly enforce workspace isolation
        if str(request.workspace_id) != str(auth_workspace_id):
            raise HTTPException(status_code=403, detail="Workspace mismatch.")

        response = await analyst_service.ask_question(
            workspace_id=str(auth_workspace_id),
            question=request.question
        )
        
        return BusinessQuestionResponse(
            answer=response["answer"],
            insights_used=response["insights_used"]
        )
    except Exception as e:
        log_business_telemetry("analyst_failures", workspace_id=str(request.workspace_id), details={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process business question."
        )
