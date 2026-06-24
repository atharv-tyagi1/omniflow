"""
Test configuration for OmniFlow backend tests.

Uses an in-memory SQLite database with type adapters for PostgreSQL-specific
column types (JSONB, pgvector Vector) that SQLite does not natively support.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy import Text, event

from backend.app.models.base import Base
from backend.app.core.database import get_db

# ---------------------------------------------------------------------------
# SQLite Type Adapters — translate Postgres-only types for the test DB
# ---------------------------------------------------------------------------
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import types as sa_types

# Teach SQLite to treat JSONB columns as plain TEXT
@event.listens_for(Base.metadata, "before_create")
def _remap_pg_types(target, connection, **kw):
    """No-op listener; actual remapping is done via compile rules below."""
    pass

from sqlalchemy.ext.compiler import compiles

@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

# pgvector Vector type
try:
    from pgvector.sqlalchemy import Vector

    @compiles(Vector, "sqlite")
    def _compile_vector_sqlite(type_, compiler, **kw):
        return "TEXT"
except ImportError:
    pass  # pgvector not installed — no Vector columns to remap

# ---------------------------------------------------------------------------
# Test Engine & Session
# ---------------------------------------------------------------------------
import os
TEST_DATABASE_URL = "sqlite+aiosqlite:///test_db.sqlite"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Clean up local test db at exit
import atexit
def cleanup_temp_db():
    try:
        os.unlink("test_db.sqlite")
    except OSError:
        pass
atexit.register(cleanup_temp_db)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Import app AFTER type adapters are registered so model metadata compiles
# ---------------------------------------------------------------------------
from backend.app.main import app

# Ensure all models are loaded into Base.metadata
import backend.app.models

app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------------------------
# Core Fixtures
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(autouse=True)
async def setup_db(request):
    """Create all tables before each test, drop them after. Skip for clean migration tests."""
    if "test_clean_migrations" in request.node.module.__name__:
        yield
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client():
    """Yield an async httpx client wired to the FastAPI test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# Auth helpers used by multiple test modules
# ---------------------------------------------------------------------------
TEST_USER_A = {
    "email": "owner_a@omniflow.ai",
    "password": "securepassword123",
    "full_name": "Owner A",
    "workspace_name": "Workspace A",
}

TEST_USER_B = {
    "email": "owner_b@omniflow.ai",
    "password": "securepassword123",
    "full_name": "Owner B",
    "workspace_name": "Workspace B",
}


class _AuthBundle:
    """Small helper carrying token + workspace_id after signup."""

    def __init__(self, token: str, workspace_id: str, user_id: str):
        self.token = token
        self.workspace_id = workspace_id
        self.user_id = user_id


async def _signup(client: AsyncClient, user_data: dict) -> _AuthBundle:
    resp = await client.post("/api/v1/auth/signup", json=user_data)
    data = resp.json()["data"]
    return _AuthBundle(
        token=data["access_token"],
        workspace_id=data["user"]["workspace_id"],
        user_id=data["user"]["id"],
    )


@pytest_asyncio.fixture
async def auth_a(async_client: AsyncClient) -> _AuthBundle:
    return await _signup(async_client, TEST_USER_A)


@pytest_asyncio.fixture
async def auth_b(async_client: AsyncClient) -> _AuthBundle:
    return await _signup(async_client, TEST_USER_B)

@pytest_asyncio.fixture
async def db():
    async with TestingSessionLocal() as session:
        yield session

from uuid import uuid4
from backend.app.models.workspace import Workspace
from backend.app.models.customer import Customer

@pytest_asyncio.fixture
async def sample_customer(db: AsyncSession):
    workspace = Workspace(id=uuid4(), name="Test Workspace", plan="free")
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    
    customer = Customer(
        id=uuid4(),
        workspace_id=workspace.id,
        name="Test Lead Customer",
        email="lead@example.com"
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return workspace, customer
