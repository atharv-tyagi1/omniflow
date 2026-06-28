import asyncio
import httpx
import time
import statistics
import uuid
import jwt
from backend.app.main import app

async def test_load_benchmark():
    print("[MULTI-WORKER BENCHMARK TEST]")
    
    # 1. Setup isolated tenant via APIs
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        email = f"bench_{uuid.uuid4()}@test.com"
        r_tenant = await client.post("/api/v1/auth/signup", json={
            "email": email, "password": "password123", "full_name": "Test Bench", "workspace_name": "Bench Workspace"
        })
        token = r_tenant.json()["data"]["access_token"]
        payload = jwt.decode(token, options={"verify_signature": False})
        workspace_id = payload["workspace_id"]
        
        h = {"Authorization": f"Bearer {token}"}
        
        r_agent = await client.post(
            f"/api/v1/workspaces/{workspace_id}/agents",
            headers=h,
            json={"name": "Test Agent Bench", "category": "test", "is_public": True}
        )
        agent_id = r_agent.json()["id"]
        
        r_key = await client.post(
            f"/api/v1/api-keys",
            headers=h,
            json={"name": "bench key", "scopes": ["agent_chat"]}
        )
        key_secret = r_key.json()["key_secret"]
        
        # Mock LLM dispatch so it returns instantly for load testing
        import backend.app.api.public.v1.agents
        async def mock_bench_dispatch(*args, **kwargs):
            await asyncio.sleep(0.01) # 10ms simulated latency
            return {"content": "mocked", "status": "success", "run_id": "123", "latency_ms": 10, "tokens_used": 100}
        backend.app.api.public.v1.agents.AgentService.dispatch = mock_bench_dispatch
        
        headers = {
            "X-Api-Key": key_secret,
        }
        
        TOTAL_REQUESTS = 200
        CONCURRENCY = 50
        
        print(f"  Sending {TOTAL_REQUESTS} requests with concurrency {CONCURRENCY}...")
        
        latencies = []
        status_codes = []
        
        sem = asyncio.Semaphore(CONCURRENCY)
        
        async def make_request(i):
            async with sem:
                start_time = time.perf_counter()
                
                req_headers = headers.copy()
                req_headers["idempotency-key"] = f"bench_{i}"
                
                resp = await client.post(
                    f"/api/public/v1/agents/{agent_id}/chat",
                    headers=req_headers,
                    json={"message": "hello", "stream": False}
                )
                
                lat = time.perf_counter() - start_time
                latencies.append(lat)
                status_codes.append(resp.status_code)
                
        start_bench = time.perf_counter()
        
        tasks = [make_request(i) for i in range(TOTAL_REQUESTS)]
        await asyncio.gather(*tasks)
        
        total_time = time.perf_counter() - start_bench
        
        successes = status_codes.count(200)
        rate_limits = status_codes.count(429)
        
        rps = TOTAL_REQUESTS / total_time
        p95 = statistics.quantiles(latencies, n=20)[18] * 1000 # in ms
        avg = statistics.mean(latencies) * 1000 # in ms
        
        print("  [BENCHMARK RESULTS]")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Throughput: {rps:.2f} req/sec")
        print(f"  Avg Latency: {avg:.2f}ms")
        print(f"  p95 Latency: {p95:.2f}ms")
        print(f"  Success (200): {successes}")
        print(f"  Rate Limited (429): {rate_limits}")
        
        # Verify Baseline Thresholds
        if rps >= 50:
            print("  [PASS] Throughput meets baseline (>50 req/s)")
        else:
            print(f"  [FAIL] Throughput below baseline ({rps:.2f} req/s)")
            
        if p95 <= 200:
            print("  [PASS] p95 latency meets baseline (<200ms)")
        else:
            print(f"  [FAIL] p95 latency failed baseline ({p95:.2f}ms)")

if __name__ == "__main__":
    asyncio.run(test_load_benchmark())
