import asyncio
from backend.app.core.database import engine
from backend.app.models.base import Base
from backend.app.models.public_api import PublicApiKey, PublicApiKeyScope, PublicApiKeyRotation, PublicWebhook, PublicApiKeyAudit

from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.ext.compiler import compiles

@compiles(TEXT, "sqlite")
def compile_text_sqlite(type_, compiler, **kw):
    return "TEXT"

from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

try:
    from pgvector.sqlalchemy import Vector
    @compiles(Vector, "sqlite")
    def compile_vector_sqlite(type_, compiler, **kw):
        return "TEXT"
except ImportError:
    pass

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_tables())
