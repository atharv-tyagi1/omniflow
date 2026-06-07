from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.ai import AIRequest
from backend.app.models.business_analyst import BusinessQuestionAudit, BusinessInsight
from backend.app.services.ai_service import AIService
from backend.app.services.business.insight_engine import InsightEngine
from backend.app.core.telemetry import log_business_telemetry

class BusinessAnalystService:
    def __init__(self, db: AsyncSession, insight_engine: InsightEngine):
        self.db = db
        self.insight_engine = insight_engine

    def _classify_question(self, question: str) -> str:
        """
        Deterministic-ish query classifier to protect against unsupported predictions.
        """
        lower_q = question.lower()
        if "will" in lower_q or "predict" in lower_q or "future" in lower_q or "next month" in lower_q:
            return "unsupported_prediction"
        if "trend" in lower_q or "increasing" in lower_q or "decreasing" in lower_q or "why" in lower_q:
            return "trend"
        return "factual"

    async def ask_question(self, workspace_id: str, question: str) -> Dict[str, Any]:
        """
        Processes an ad-hoc business question.
        """
        classification = self._classify_question(question)
        
        # Persist audit
        audit = BusinessQuestionAudit(
            workspace_id=workspace_id,
            question=question,
            classification=classification
        )
        self.db.add(audit)
        await self.db.commit()
        
        if classification == "unsupported_prediction":
            log_business_telemetry("unsupported_query_rejected", workspace_id=workspace_id)
            return {
                "answer": "Insufficient evidence. The Business Analyst cannot make forward-looking predictions.",
                "insights_used": []
            }
            
        # Ensure we have fresh insights
        insights = await self.insight_engine.generate_insights(workspace_id)
        
        if not insights:
             return {
                "answer": "Not enough data available to answer this question currently.",
                "insights_used": []
            }
        
        # Format insights for LLM presentation
        insight_context = "\n".join([f"- {i.title}: {i.description} (Confidence: {i.confidence})" for i in insights[:10]])
        
        prompt = f"""
        You are a presentation layer for a business analyst engine.
        Question: {question}
        
        Available Data Facts:
        {insight_context}
        
        Answer the question using ONLY the provided facts. Do not invent any metrics or make predictions.
        """
        
        try:
            req = AIRequest(
                user_query=prompt,
                system_prompt="You are a business intelligence assistant."
            )
            response_obj = await AIService.generate_response(req)
            answer = response_obj.content
        except Exception as e:
            log_business_telemetry("analyst_failures", workspace_id=workspace_id, details={"error": str(e)})
            answer = "Failed to generate presentation layer response."
            
        return {
            "answer": answer,
            "insights_used": [str(i.id) for i in insights[:10]]
        }
