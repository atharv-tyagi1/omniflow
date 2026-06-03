from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.dataset import Dataset
from backend.app.models.dataset_query import DatasetQuery
from backend.app.repositories.dataset_repository import DatasetRepository
from backend.app.core.exceptions import NotFoundError


class DatasetService:
    @staticmethod
    async def create_dataset(
        db: AsyncSession,
        workspace_id: UUID,
        name: str,
        file_url: str,
        row_count: Optional[int] = None,
        column_count: Optional[int] = None,
    ) -> Dataset:
        return await DatasetRepository.create(
            db=db,
            workspace_id=workspace_id,
            name=name,
            file_url=file_url,
            row_count=row_count,
            column_count=column_count,
        )

    @staticmethod
    async def get_dataset(
        db: AsyncSession, dataset_id: UUID, workspace_id: UUID
    ) -> Dataset:
        dataset = await DatasetRepository.get_by_id(db, dataset_id, workspace_id)
        if not dataset:
            raise NotFoundError("Dataset not found")
        return dataset

    @staticmethod
    async def list_datasets(db: AsyncSession, workspace_id: UUID) -> List[Dataset]:
        return await DatasetRepository.list_by_workspace(db, workspace_id)

    @staticmethod
    async def query_dataset(
        db: AsyncSession, workspace_id: UUID, dataset_id: UUID, question: str
    ) -> DatasetQuery:
        # Validate ownership
        dataset = await DatasetService.get_dataset(db, dataset_id, workspace_id)

        import pandas as pd
        from backend.app.core.ai.gemini_client import GeminiClient
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Load dataset into pandas
            # pandas can read from URLs directly. For MVP, we limit rows to avoid massive memory usage
            df = pd.read_csv(dataset.file_url, nrows=100)

            # Create a preview with schema and first few rows
            schema_info = df.dtypes.to_dict()
            schema_str = ", ".join(
                [f"{col} ({dtype})" for col, dtype in schema_info.items()]
            )
            head_str = df.head(5).to_string(index=False)

            data_preview = f"Columns: {schema_str}\n\nSample Data:\n{head_str}"

            # Analyze using Gemini
            analysis_result = await GeminiClient.analyze_dataset(data_preview, question)

            if analysis_result["error"]:
                answer = (
                    "I'm sorry, I encountered an error while analyzing this dataset."
                )
                chart_config = {"type": "bar", "data": []}
                logger.error(f"Gemini analysis error: {analysis_result['error']}")
            else:
                answer = analysis_result["response"]
                chart_config = analysis_result["chart_config"]

        except Exception as e:
            logger.error(f"Failed to process dataset query: {e}")
            answer = "I'm sorry, I could not read or analyze this dataset."
            chart_config = {"type": "bar", "data": []}

        return await DatasetRepository.add_query(
            db=db,
            dataset_id=dataset_id,
            question=question,
            answer=answer,
            chart_config=chart_config,
        )
