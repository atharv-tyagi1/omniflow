import os
import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic import command

@pytest.mark.asyncio
async def test_postgres_clean_start_migration():
    """
    Smoke test to prove that migrations cleanly apply to PostgreSQL.
    Skips locally if POSTGRES_TEST_URL is not provided, but fails in CI.
    """
    db_url = os.environ.get("POSTGRES_TEST_URL")
    if not db_url:
        if os.environ.get("CI"):
            pytest.fail("POSTGRES_TEST_URL must be set in CI environments.")
        else:
            pytest.skip("POSTGRES_TEST_URL not set. Skipping Postgres migration smoke test.")
    
    # Load Alembic config
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    try:
        # Run upgrade head
        command.upgrade(alembic_cfg, "head")
        
        # Verify schema
        # We need a synchronous connection for the schema check here
        sync_url = db_url.replace("+asyncpg", "")
        engine = sa.create_engine(sync_url)
        with engine.connect() as conn:
            # Verify the composite unique constraint on handoffs table
            result = conn.execute(sa.text(
                "SELECT indexname FROM pg_indexes WHERE tablename = 'handoffs' AND indexname = 'uq_handoff_source_message'"
            )).fetchone()
            
            assert result is not None, "uq_handoff_source_message unique index missing in Postgres migration."

            # Verify JSONB field exists on conversations
            result_jsonb = conn.execute(sa.text(
                "SELECT data_type FROM information_schema.columns WHERE table_name = 'conversations' AND column_name = 'current_state'"
            )).fetchone()
            
            assert result_jsonb is not None
            assert result_jsonb[0] == "jsonb", "current_state is not JSONB in Postgres."

        assert True
    except Exception as e:
        pytest.fail(f"Postgres migration smoke test failed: {e}")
