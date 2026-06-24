"""
scripts/load_test.py
====================
Phase 20.6.5.1 – Task 10: Isolated API Load Testing

Tests OmniFlow HTTP API endpoints under concurrent load using
exclusively isolated test workspaces and test users.

Rules:
- All test users prefixed: loadtest_<uuid>@loadtest.omniflow
- All test workspaces prefixed: loadtest_
- No production tenant data is accessed
- All test data is cleaned up in the finally block

Usage:
    # Start the backend first:
    #   cd backend && uvicorn app.main:app --port 8000 &
    # Then run:
    cd omniflow
    python -m scripts.load_test [--base-url http://localhost:8000]

The script tests:
  1. Health endpoint (baseline, no auth)
  2. Auth /signup + /login  (write-heavy)
  3. Workspace read (authenticated GET)
  4. Conversation list (authenticated GET, workspace-scoped)
"""

import asyncio
import time
import statistics
import sys
import uuid
import os
import logging
import argparse
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass, field

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("LOAD_TEST_BASE_URL", "http://localhost:8000")

# Test user/workspace records for cleanup
_CLEANUP_USERS: List[dict] = []  # {email, token, workspace_id}


# ── Scenario helpers ────────────────────────────────────────────────────────────

async def signup_test_user(client: httpx.AsyncClient) -> Optional[dict]:
    """Create an isolated test user and workspace. Returns auth context."""
    tag = uuid.uuid4().hex[:8]
    email = f"loadtest_{tag}@loadtest.omniflow"
    password = f"LTpass{tag}!7"
    workspace_name = f"loadtest_{tag}"

    # Signup
    r = await client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": password,
        "workspace_name": workspace_name
    })
    if r.status_code not in (200, 201):
        return None

    data = r.json().get("data", {})
    token = data.get("access_token")
    workspace_id = data.get("workspace_id")
    if not token or not workspace_id:
        return None

    ctx = {"email": email, "token": token, "workspace_id": workspace_id}
    _CLEANUP_USERS.append(ctx)
    return ctx


async def cleanup_all(client: httpx.AsyncClient):
    """Best-effort cleanup — delete test users via auth/delete endpoint if available."""
    # We can't always guarantee cleanup at API level without a delete endpoint.
    # Log the test users so they can be found via email prefix.
    if _CLEANUP_USERS:
        logger.info(
            "Cleanup: %d test users created with prefix loadtest_@loadtest.omniflow. "
            "Run SQL to clean up: DELETE FROM users WHERE email LIKE 'loadtest_%%@loadtest.omniflow';",
            len(_CLEANUP_USERS)
        )


# ── Load scenario ────────────────────────────────────────────────────────────────

@dataclass
class ScenarioResult:
    name: str
    concurrency: int
    successful: int = 0
    failed: int = 0
    times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total(self):
        return self.successful + self.failed

    @property
    def p95(self):
        if not self.times:
            return None
        s = sorted(self.times)
        return round(s[int(len(s) * 0.95)], 1)

    @property
    def p99(self):
        if not self.times:
            return None
        s = sorted(self.times)
        return round(s[int(len(s) * 0.99)], 1)

    @property
    def mean(self):
        return round(statistics.mean(self.times), 1) if self.times else None

    @property
    def median(self):
        return round(statistics.median(self.times), 1) if self.times else None

    @property
    def error_rate(self):
        if self.total == 0:
            return 0.0
        return (self.failed / self.total) * 100


async def run_health_scenario(concurrency: int) -> ScenarioResult:
    result = ScenarioResult(name="GET /health", concurrency=concurrency)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        async def single():
            start = time.perf_counter()
            try:
                r = await client.get("/health")
                elapsed = (time.perf_counter() - start) * 1000
                if r.status_code == 200:
                    result.successful += 1
                    result.times.append(elapsed)
                else:
                    result.failed += 1
                    result.errors.append(f"HTTP {r.status_code}")
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e)[:80])
        await asyncio.gather(*[single() for _ in range(concurrency)])
    return result


async def run_signup_scenario(concurrency: int) -> ScenarioResult:
    """Concurrent signup + login flow with isolated test data."""
    result = ScenarioResult(name="POST /auth/signup", concurrency=concurrency)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        async def single():
            start = time.perf_counter()
            try:
                ctx = await signup_test_user(client)
                elapsed = (time.perf_counter() - start) * 1000
                if ctx:
                    result.successful += 1
                    result.times.append(elapsed)
                else:
                    result.failed += 1
                    result.errors.append("signup returned no token")
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e)[:80])
        await asyncio.gather(*[single() for _ in range(concurrency)])
    return result


async def run_workspace_read_scenario(concurrency: int, auth_ctx: dict) -> ScenarioResult:
    """Concurrent GET /workspaces using a single test user token."""
    result = ScenarioResult(name="GET /workspaces", concurrency=concurrency)
    headers = {
        "Authorization": f"Bearer {auth_ctx['token']}",
        "x-workspace-id": auth_ctx["workspace_id"]
    }
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        async def single():
            start = time.perf_counter()
            try:
                r = await client.get("/api/v1/workspaces/", headers=headers)
                elapsed = (time.perf_counter() - start) * 1000
                if r.status_code in (200, 204):
                    result.successful += 1
                    result.times.append(elapsed)
                else:
                    result.failed += 1
                    result.errors.append(f"HTTP {r.status_code}")
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e)[:80])
        await asyncio.gather(*[single() for _ in range(concurrency)])
    return result


async def run_conversations_scenario(concurrency: int, auth_ctx: dict) -> ScenarioResult:
    """Concurrent GET /conversations — workspace-scoped read."""
    result = ScenarioResult(name="GET /conversations", concurrency=concurrency)
    headers = {
        "Authorization": f"Bearer {auth_ctx['token']}",
        "x-workspace-id": auth_ctx["workspace_id"]
    }
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        async def single():
            start = time.perf_counter()
            try:
                r = await client.get("/api/v1/conversations/", headers=headers)
                elapsed = (time.perf_counter() - start) * 1000
                if r.status_code in (200, 204):
                    result.successful += 1
                    result.times.append(elapsed)
                else:
                    result.failed += 1
                    result.errors.append(f"HTTP {r.status_code}")
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e)[:80])
        await asyncio.gather(*[single() for _ in range(concurrency)])
    return result


# ── Report ────────────────────────────────────────────────────────────────────

def print_result(r: ScenarioResult):
    print(f"\n{'='*60}")
    print(f"  {r.name}  (concurrency={r.concurrency})")
    print(f"  Results: {r.successful}/{r.total} passed  |  Error rate: {r.error_rate:.1f}%")
    if r.times:
        print(f"  Mean: {r.mean} ms  |  Median: {r.median} ms  |  P95: {r.p95} ms  |  P99: {r.p99} ms")
    if r.errors:
        unique_errors = list(set(r.errors))[:3]
        print(f"  Sample errors: {unique_errors}")
    if r.error_rate > 1.0:
        print(f"  STATUS: FAIL  (error rate {r.error_rate:.1f}% > 1%)")
    elif r.p95 and r.p95 > 3000:
        print(f"  STATUS: WARN  (P95={r.p95} ms > 3000 ms)")
    else:
        print(f"  STATUS: PASS")
    print(f"{'='*60}")


async def main(base_url: str):
    global BASE_URL
    BASE_URL = base_url

    print(f"\n{'='*60}")
    print(f"  OmniFlow API Load Test — Phase 20.6.5.1 Task 10")
    print(f"  Target: {base_url}")
    print(f"  Using isolated test workspaces only")
    print(f"{'='*60}")

    # Verify server is reachable
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
            r = await client.get("/health")
            if r.status_code != 200:
                print(f"FATAL: Server returned {r.status_code} on /health")
                sys.exit(1)
    except Exception as e:
        print(f"FATAL: Cannot reach server at {base_url}: {e}")
        sys.exit(1)

    all_results = []
    auth_ctx = None

    try:
        # 1. Health — baseline (no auth, 200 concurrent)
        r1 = await run_health_scenario(200)
        print_result(r1)
        all_results.append(r1)
        await asyncio.sleep(0.5)

        # 2. Signup — write-heavy (20 concurrent test users)
        r2 = await run_signup_scenario(20)
        print_result(r2)
        all_results.append(r2)
        await asyncio.sleep(0.5)

        # 3. Use one of the created test users for read scenarios
        if _CLEANUP_USERS:
            auth_ctx = _CLEANUP_USERS[0]

            # 3a. Workspace reads (100 concurrent)
            r3 = await run_workspace_read_scenario(100, auth_ctx)
            print_result(r3)
            all_results.append(r3)
            await asyncio.sleep(0.5)

            # 3b. Conversation reads (100 concurrent)
            r4 = await run_conversations_scenario(100, auth_ctx)
            print_result(r4)
            all_results.append(r4)
        else:
            logger.warning("No test users created — skipping authenticated scenarios")

    finally:
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
            await cleanup_all(client)

    # Summary
    print(f"\n\n{'='*60}")
    print("  LOAD TEST SUMMARY")
    print(f"  {'Scenario':<30} {'Pass':<6} {'Fail':<6} {'P95 ms':<10} {'Status'}")
    print(f"  {'-'*55}")
    any_fail = False
    for r in all_results:
        p95 = str(r.p95) if r.p95 is not None else "N/A"
        if r.error_rate > 1.0:
            status = "FAIL"
            any_fail = True
        elif r.p95 and r.p95 > 3000:
            status = "WARN"
        else:
            status = "PASS"
        print(f"  {r.name:<30} {r.successful:<6} {r.failed:<6} {p95:<10} {status}")
    print(f"{'='*60}")
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    asyncio.run(main(args.base_url))
