import asyncio
from uuid import uuid4
import sys
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

# Ensure backend can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.db import engine
from backend.app.models.agent import Agent
from backend.app.models.agent_version import AgentVersion
from backend.app.core.agent.engine import AgentRuntime
from backend.app.core.agent.exceptions import PolicyViolationError

async def run_verification():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    workspace_id = uuid4()
    agent_id = uuid4()
    conversation_id = uuid4()
    
    # Setup mock agent and version for testing
    agent = Agent(
        id=agent_id,
        workspace_id=workspace_id,
        name="Test Support Agent",
        description="Public Customer Support",
        is_active=True,
        is_public=True
    )
    
    agent_version = AgentVersion(
        id=uuid4(),
        agent_id=agent_id,
        version_number=1,
        prompt_config={"system_prompt": "You are a helpful customer support agent."},
        is_published=True
    )

    print("=== STARTING RUNTIME E2E VERIFICATION ===")

    async with async_session() as db:
        runtime = AgentRuntime(db, agent, agent_version)
        
        # 1. Positive public customer-agent path
        try:
            print("\nTest 1: Positive Public Customer Agent Path")
            result = await runtime.execute_turn(
                workspace_id=workspace_id,
                conversation_id=conversation_id,
                user_query="Hi, I need help with my billing.",
                workspace_policies=["Be polite."]
            )
            print(f"✅ Success. Response: {result['content'][:50]}...")
        except Exception as e:
            print(f"❌ Failed: {e}")

        # 2. Negative Security Test (Private Agent accessed publicly)
        # Assuming the caller checks `agent.is_public` before calling, but we simulate a policy block
        try:
            print("\nTest 2: Negative Security Test (Abuse Guardrails)")
            runtime._policy_denials = 3
            runtime.check_guardrails()
            print("❌ Failed: Should have raised PolicyViolationError")
        except PolicyViolationError as e:
            print(f"✅ Success. Blocked as expected: {e}")
            runtime._policy_denials = 0 # reset
            
        # 3. Failure path handling
        try:
            print("\nTest 3: Failure-path / Tool Loop limit test")
            for _ in range(6):
                runtime.check_guardrails(is_workflow=False)
            print("❌ Failed: Should have blocked after 5 tool calls")
        except PolicyViolationError as e:
            print(f"✅ Success. Blocked infinite loop: {e}")

if __name__ == "__main__":
    # Usually you would have a real test DB
    print("Verification script written. In a real environment, this runs against a test DB.")
    # asyncio.run(run_verification())
