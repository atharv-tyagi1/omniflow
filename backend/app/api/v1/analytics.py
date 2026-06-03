from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.services.dashboard_service import DashboardService

from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve operational KPIs, chart data, and recent activity for the workspace dashboard.
    """
    try:
        data = await DashboardService.get_dashboard_metrics(db, current_user.workspace_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
