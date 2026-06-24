"""Add HNSW index to document_chunks

Revision ID: 88e3fe034baa
Revises: a81246da229c
Create Date: 2026-06-24 19:42:47.820914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88e3fe034baa'
down_revision: Union[str, Sequence[str], None] = 'a81246da229c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL to create the HNSW index for pgvector
    op.execute(
        "CREATE INDEX idx_chunks_embedding "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding;")
