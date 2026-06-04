from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.services.dashboard_service import DashboardService

from backend.app.middleware.auth import get_current_user
from backend.app.middleware.workspace_guard import get_current_workspace_id
from backend.app.models.user import User

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(
    workspace_id: UUID = Depends(get_current_workspace_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve operational KPIs, chart data, and recent activity for the workspace dashboard.
    """
    try:
        data = await DashboardService.get_dashboard_metrics(db, workspace_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
