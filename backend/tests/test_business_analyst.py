import pytest
from unittest.mock import AsyncMock, patch
import uuid

from backend.app.services.business.business_analyst_service import BusinessAnalystService
from backend.app.services.business.insight_engine import InsightEngine
from backend.app.services.ai_service import AIService
from backend.app.models.business_analyst import BusinessInsight
from backend.app.schemas.ai import AIResponse

@pytest.mark.asyncio
async def test_business_analyst_classifier_blocks_prediction():
    mock_db = AsyncMock()
    mock_insight_engine = AsyncMock(spec=InsightEngine)
    
    service = BusinessAnalystService(db=mock_db, insight_engine=mock_insight_engine)
    
    result = await service.ask_question("test_workspace", "What will happen to sales next month?")
    
    assert result["answer"] == "Insufficient evidence. The Business Analyst cannot make forward-looking predictions."
    assert result["insights_used"] == []
    
    # Ensure no insights were generated or fetched
    mock_insight_engine.generate_insights.assert_not_called()

@pytest.mark.asyncio
async def test_business_analyst_factual_query():
    mock_db = AsyncMock()
    mock_insight_engine = AsyncMock(spec=InsightEngine)
    
    # Mock some insights
    insight = BusinessInsight(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        title="Tickets increased by 20%",
        description="Ticket count went from 100 to 120",
        confidence=95.0,
        priority="high"
    )
    mock_insight_engine.generate_insights.return_value = [insight]
    
    service = BusinessAnalystService(db=mock_db, insight_engine=mock_insight_engine)
    
    with patch('backend.app.services.ai_service.AIService.generate_response', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(
            content="Based on the facts, tickets increased by 20%.",
            latency_ms=100.0,
            tokens_used=50,
            sources=[]
        )
        
        result = await service.ask_question("test_workspace", "Why are support tickets increasing?")
        
        assert "tickets increased by 20%" in result["answer"]
        assert len(result["insights_used"]) == 1
        assert result["insights_used"][0] == str(insight.id)
        mock_ai.assert_called_once()
