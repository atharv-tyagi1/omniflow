from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, List, Dict, Any

from backend.app.models.dataset import Dataset
from backend.app.models.dataset_query import DatasetQuery


class DatasetRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        workspace_id: UUID,
        name: str,
        file_url: str,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None
    ) -> Dataset:
        db_obj = Dataset(
            workspace_id=workspace_id,
            name=name,
            file_url=file_url,
            row_count=row_count,
            column_count=column_count
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    @staticmethod
    async def get_by_id(db: AsyncSession, dataset_id: UUID, workspace_id: UUID) -> Optional[Dataset]:
        result = await db.execute(
            select(Dataset)
            .where(Dataset.id == dataset_id, Dataset.workspace_id == workspace_id)
            .options(selectinload(Dataset.queries))
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_workspace(db: AsyncSession, workspace_id: UUID) -> List[Dataset]:
        result = await db.execute(
            select(Dataset)
            .where(Dataset.workspace_id == workspace_id)
            .order_by(Dataset.uploaded_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_query(
        db: AsyncSession,
        *,
        dataset_id: UUID,
        question: str,
        answer: Optional[str] = None,
        chart_config: Optional[Dict[str, Any]] = None
    ) -> DatasetQuery:
        db_obj = DatasetQuery(
            dataset_id=dataset_id,
            question=question,
            answer=answer,
            chart_config=chart_config
        )
        db.add(db_obj)
        await db.flush()
        return db_obj
