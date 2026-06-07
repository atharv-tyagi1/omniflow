import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.config import Config
from alembic import command

@pytest.mark.asyncio
async def test_clean_start_migration():
    """
    Smoke test to prove that a completely fresh database can run all migrations cleanly.
    This simulates spinning up a new environment.
    """
    # Use a separate in-memory sqlite DB for the clean test
    # SQLAlchemy's Alembic implementation generally works well with sqlite for basic schema validation
    # Although some advanced PG features (like pg_trgm) might be mocked or ignored.
    
    # We will use an actual file temporarily to allow Alembic synchronous commands to run on it
    test_db_url = "sqlite:///./test_clean_start.db"
    if os.path.exists("./test_clean_start.db"):
        os.remove("./test_clean_start.db")

    try:
        # Load Alembic config
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
        
        try:
            # Load Alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
            
            # Run upgrade head
            command.upgrade(alembic_cfg, "head")
            
            # If it completes without raising an exception, the migrations are clean.
            assert True
        finally:
            pass
    finally:
        # Clean up
        if os.path.exists("./test_clean_start.db"):
            os.remove("./test_clean_start.db")
