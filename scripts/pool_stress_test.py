"""
scripts/pool_stress_test.py
============================
Phase 20.6.5.1 – Task 7: Database Pool Stress Testing

Tests the PostgreSQL connection pool under concurrent simulated load.

Rules:
- Uses ONLY test workspaces / test users (prefix: pooltest_)
- Never reads or writes production tenant data
- Cleans up all test data on exit (via finally block)
- Targets: 100, 250, 500 concurrent connection acquisitions

Usage:
    cd omniflow
    python -m scripts.pool_stress_test

Dependencies: asyncpg, sqlalchemy[asyncio], asyncio -- already in requirements.txt
"""

import asyncio
import time
import statistics
import sys
import uuid
import os
import logging
from datetime import datetime, timezone
from typing import List
from pathlib import Path

# Load env
root_env = Path(__file__).parent.parent / ".env"
from dotenv import load_dotenv
load_dotenv(root_env, override=False)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL or "postgresql" not in DATABASE_URL:
    print("FATAL: DATABASE_URL must be a PostgreSQL connection string.")
    print("Current value:", DATABASE_URL[:40] if DATABASE_URL else "(empty)")
    sys.exit(1)

# Dedicated stress-test engine -- separate from production engine
STRESS_ENGINE = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=5,        # same as production
    max_overflow=10,    # same as production
    pool_timeout=30,    # same as production
)

StressSession = async_sessionmaker(
    bind=STRESS_ENGINE,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

# All test workspaces are identified by this prefix so cleanup is safe
TEST_WORKSPACE_PREFIX = "pooltest_"
_CREATED_WORKSPACE_IDS: List[str] = []


async def create_test_workspace(db: AsyncSession, label: str) -> str:
    """Insert a throwaway workspace row and return its id."""
    ws_id = str(uuid.uuid4())
    name = f"{TEST_WORKSPACE_PREFIX}{label}_{ws_id[:8]}"
    await db.execute(
        text(
            "INSERT INTO workspaces (id, name, created_at, updated_at) "
            "VALUES (:id, :name, :now, :now)"
        ),
        {"id": ws_id, "name": name, "now": datetime.now(timezone.utc)},
    )
    await db.commit()
    _CREATED_WORKSPACE_IDS.append(ws_id)
    return ws_id


async def cleanup_test_data():
    """Delete all rows created during this run. Called unconditionally in finally."""
    if not _CREATED_WORKSPACE_IDS:
        return
    async with StressSession() as db:
        for ws_id in _CREATED_WORKSPACE_IDS:
            await db.execute(text("DELETE FROM workspaces WHERE id = :id"), {"id": ws_id})
        await db.commit()
    logger.info("Cleanup complete -- %d test workspaces removed.", len(_CREATED_WORKSPACE_IDS))


async def single_db_transaction(worker_id: int, ws_id: str) -> dict:
    """
    Acquires a session from the pool, executes a simple scoped read,
    records timing, and releases back to pool.
    """
    start = time.perf_counter()
    error = None
    try:
        async with StressSession() as db:
            result = await db.execute(
                text("SELECT id, name FROM workspaces WHERE id = :id"),
                {"id": ws_id},
            )
            row = result.fetchone()
            assert row is not None, f"Workspace {ws_id} not found"
    except Exception as e:
        error = str(e)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return {"worker_id": worker_id, "elapsed_ms": elapsed_ms, "error": error}


async def run_load_scenario(concurrency: int, ws_id: str) -> dict:
    """
    Fires `concurrency` concurrent transactions against the pool and returns
    aggregate statistics.
    """
    logger.info("Starting load scenario: %d concurrent tasks", concurrency)
    tasks = [single_db_transaction(i, ws_id) for i in range(concurrency)]
    t0 = time.perf_counter()
    results = await asyncio.gather(*tasks, return_exceptions=False)
    total_wall_ms = (time.perf_counter() - t0) * 1000

    times = [r["elapsed_ms"] for r in results if r["error"] is None]
    errors = [r for r in results if r["error"] is not None]

    return {
        "concurrency": concurrency,
        "total_tasks": concurrency,
        "successful": len(times),
        "failed": len(errors),
        "errors": [e["error"] for e in errors][:5],
        "total_wall_ms": round(total_wall_ms, 1),
        "mean_ms": round(statistics.mean(times), 1) if times else None,
        "median_ms": round(statistics.median(times), 1) if times else None,
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 1) if times else None,
        "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 1) if times else None,
        "min_ms": round(min(times), 1) if times else None,
        "max_ms": round(max(times), 1) if times else None,
    }


def print_scenario_result(result: dict):
    c = result["concurrency"]
    ok = result["successful"]
    fail = result["failed"]
    print(f"\n{'='*60}")
    print(f"  Concurrency: {c} simultaneous connections")
    print(f"  Results: {ok} passed / {fail} failed")
    print(f"  Wall time: {result['total_wall_ms']} ms")
    if result["mean_ms"] is not None:
        print(f"  Mean:   {result['mean_ms']} ms")
        print(f"  Median: {result['median_ms']} ms")
        print(f"  P95:    {result['p95_ms']} ms")
        print(f"  P99:    {result['p99_ms']} ms")
        print(f"  Min:    {result['min_ms']} ms")
        print(f"  Max:    {result['max_ms']} ms")
    if result["errors"]:
        print(f"  Errors (first {len(result['errors'])}):")
        for e in result["errors"]:
            print(f"    - {e}")
    fail_pct = (fail / c) * 100
    if fail_pct > 1.0:
        print(f"  STATUS: FAIL  ({fail_pct:.1f}% failure rate > 1% threshold)")
    elif result["p95_ms"] and result["p95_ms"] > 2000:
        print(f"  STATUS: WARN  (P95 latency {result['p95_ms']} ms > 2000 ms SLA)")
    else:
        print(f"  STATUS: PASS")
    print(f"{'='*60}")


async def main():
    print("\n" + "="*60)
    print("  OmniFlow PostgreSQL Pool Stress Test")
    print("  Phase 20.6.5.1 - Task 7")
    print("  Pool config: pool_size=5, max_overflow=10, pool_timeout=30")
    print("  IMPORTANT: Uses isolated test workspaces only")
    print("="*60)

    all_results = []
    try:
        async with StressSession() as db:
            ws_id = await create_test_workspace(db, "stress")
        logger.info("Test workspace created: %s", ws_id)

        for concurrency in [100, 250, 500]:
            result = await run_load_scenario(concurrency, ws_id)
            print_scenario_result(result)
            all_results.append(result)
            await asyncio.sleep(1)  # cool-down between scenarios

    finally:
        await cleanup_test_data()
        await STRESS_ENGINE.dispose()

    print("\n\n" + "="*60)
    print("  SUMMARY")
    print(f"  {'Concurrency':<15} {'Passed':<10} {'Failed':<10} {'P95 ms':<12} {'Status'}")
    print(f"  {'-'*55}")
    for r in all_results:
        p95 = r["p95_ms"] or "N/A"
        fail_pct = (r["failed"] / r["concurrency"]) * 100
        if fail_pct > 1 or (isinstance(p95, float) and p95 > 2000):
            status = "FAIL" if fail_pct > 1 else "WARN"
        else:
            status = "PASS"
        print(f"  {r['concurrency']:<15} {r['successful']:<10} {r['failed']:<10} {str(p95):<12} {status}")
    print("="*60)

    any_failed = any(r["failed"] / r["concurrency"] > 0.01 for r in all_results)
    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
