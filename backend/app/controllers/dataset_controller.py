from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.services.dataset_service import DatasetService
from backend.app.models.dataset import Dataset
from backend.app.models.dataset_query import DatasetQuery


class DatasetController:
    @staticmethod
    async def upload(
        db: AsyncSession,
        workspace_id: UUID,
        name: str,
        file_url: str,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
    ) -> Dataset:
        return await DatasetService.create_dataset(
            db=db,
            workspace_id=workspace_id,
            name=name,
            file_url=file_url,
            row_count=row_count,
            column_count=column_count,
        )

    @staticmethod
    async def get_all(db: AsyncSession, workspace_id: UUID) -> List[Dataset]:
        return await DatasetService.list_datasets(db, workspace_id)

    @staticmethod
    async def get_by_id(
        db: AsyncSession, dataset_id: UUID, workspace_id: UUID
    ) -> Dataset:
        return await DatasetService.get_dataset(db, dataset_id, workspace_id)

    @staticmethod
    async def ask_question(
        db: AsyncSession, workspace_id: UUID, dataset_id: UUID, question: str
    ) -> DatasetQuery:
        return await DatasetService.query_dataset(
            db=db, workspace_id=workspace_id, dataset_id=dataset_id, question=question
        )
