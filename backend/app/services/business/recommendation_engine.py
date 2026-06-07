import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.schemas.ai import AIRequest
from backend.app.models.business_analyst import BusinessInsight, BusinessRecommendation
from backend.app.services.ai_service import AIService
from backend.app.core.telemetry import log_business_telemetry

ENGINE_VERSION = "1.0.0"

class RecommendationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_recommendations(self, workspace_id: str, insight_ids: List[uuid.UUID]) -> List[BusinessRecommendation]:
        """
        Takes deterministic insights and uses AIService to generate readable, actionable recommendations.
        """
        recommendations = []
        
        stmt = select(BusinessInsight).where(
            BusinessInsight.workspace_id == workspace_id,
            BusinessInsight.id.in_(insight_ids)
        )
        res_insights = await self.db.execute(stmt)
        insights = res_insights.scalars().all()
        
        for insight in insights:
            # Skip if recommendation already exists for this insight
            res_existing = await self.db.execute(select(BusinessRecommendation).where(BusinessRecommendation.insight_id == insight.id))
            if res_existing.scalar():
                continue

            # Deterministic rule IDs
            rule_id = f"rule_{insight.category}_{insight.priority}"

            # LLM acts purely as presentation layer to write the recommendation
            prompt = f"""
            You are a presentation layer translating raw data into an executive recommendation.
            Insight: {insight.title}
            Description: {insight.description}
            Confidence: {insight.confidence}
            Priority: {insight.priority}
            
            Based on this exact data, provide a 1-sentence actionable recommendation and a 1-sentence rationale. 
            Do NOT invent any metrics. Format your response exactly as:
            Recommendation: <text>
            Rationale: <text>
            """
            try:
                request = AIRequest(
                    user_query=prompt,
                    system_prompt="You are a presentation layer translating raw data into an executive recommendation."
                )
                response_obj = await AIService.generate_response(request)
                response = response_obj.content
                
                # Parse response
                if response:
                    for line in response.split("\n"):
                        if line.startswith("Recommendation:"):
                            rec_text = line.replace("Recommendation:", "").strip()
                        elif line.startswith("Rationale:"):
                            rat_text = line.replace("Rationale:", "").strip()

            except Exception as e:
                log_business_telemetry("recommendation_generation_failure", workspace_id=workspace_id, details={"error": str(e), "insight_id": str(insight.id)})
                # Deterministic fallback text by category
                cat = insight.category.lower() if insight.category else "general"
                if "sales" in cat:
                    rec_text = f"Investigate sales conversion pipeline regarding: {insight.title}"
                elif "support" in cat:
                    rec_text = f"Review support resolution metrics regarding: {insight.title}"
                elif "customer_care" in cat:
                    rec_text = f"Audit customer care interactions regarding: {insight.title}"
                elif "retention" in cat:
                    rec_text = f"Analyze churn risk factors regarding: {insight.title}"
                elif "sentiment" in cat:
                    rec_text = f"Address customer sentiment shifts regarding: {insight.title}"
                else:
                    rec_text = f"Review the trend for {insight.title}."
                
                rat_text = f"Automated deterministic recommendation triggered due to AI presentation layer unavailability."

            recommendation = BusinessRecommendation(
                workspace_id=workspace_id,
                insight_id=insight.id,
                recommendation=rec_text,
                rationale=rat_text,
                confidence=insight.confidence,  # Inherit confidence
                priority=insight.priority,      # Inherit priority
                recommendation_engine_version=ENGINE_VERSION,
                recommendation_rule_id=rule_id,
                effectiveness_status="unknown"
            )
            self.db.add(recommendation)
            recommendations.append(recommendation)

        await self.db.commit()
        
        if recommendations:
            log_business_telemetry(
                "recommendations_generated", 
                workspace_id=workspace_id, 
                details={"count": len(recommendations)}
            )
            
        return recommendations
