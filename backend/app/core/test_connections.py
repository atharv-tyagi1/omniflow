import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text
import httpx
from dotenv import load_dotenv

# Ensure backend folder is in path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from backend.app.core.config import settings


async def test_database() -> bool:
    print("\n--- Testing Database Connection ---")
    print(
        f"Connecting to: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}"
    )
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            if val == 1:
                print(
                    "[SUCCESS] Database connection successful! (Query 'SELECT 1' returned 1)"
                )
                return True
            else:
                print(f"[FAIL] Database query returned unexpected value: {val}")
                return False
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False


async def test_supabase() -> bool:
    print("\n--- Testing Supabase Connection ---")
    print(f"URL: {settings.SUPABASE_URL}")
    try:
        # We can send a request to the supabase rest endpoint
        async with httpx.AsyncClient() as client:
            headers = {"apikey": settings.SUPABASE_ANON_KEY}
            response = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/", headers=headers, timeout=10.0
            )
            if response.status_code in [200, 204, 401]:
                print(
                    f"[SUCCESS] Supabase connection successful! Status Code: {response.status_code}"
                )
                return True
            else:
                print(
                    f"[FAIL] Supabase API returned status code: {response.status_code}"
                )
                return False
    except Exception as e:
        print(f"[FAIL] Supabase connection failed: {e}")
        return False


async def test_gemini() -> bool:
    print("\n--- Testing Gemini AI Connection ---")
    key = settings.GEMINI_API_KEY
    if not key or key == "your-gemini-api-key" or key == "":
        print("[WARNING] No Gemini API Key provided. Skipping actual API call.")
        return False

    try:
        from google import genai

        # Initialize the modern Gemini API Client
        client = genai.Client(api_key=key)
        # Call a lightweight model (gemini-2.5-flash or gemini-1.5-flash)
        # The master build instructions say primary LLM is Gemini 2.5 Pro. We can use gemini-2.5-flash for a quick test if supported.
        # Let's test with gemini-2.5-flash
        print("Sending test request to Gemini API...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents='Respond with the single word "READY".',
        )
        text_resp = response.text.strip()
        print(f"Gemini Response: {text_resp}")
        if "READY" in text_resp.upper():
            print("[SUCCESS] Gemini AI connection successful!")
            return True
        else:
            print("[FAIL] Gemini AI returned unexpected response.")
            return False
    except Exception as e:
        print(f"[FAIL] Gemini AI connection failed: {e}")
        return False


async def main():
    print("========================================")
    print("OmniFlow Connection Diagnostics")
    print("========================================")

    db_ok = await test_database()
    supabase_ok = await test_supabase()
    gemini_ok = await test_gemini()

    print("\n========================================")
    print("Diagnostic Summary:")
    print(f"Database: {'[SUCCESS] OK' if db_ok else '[FAIL] FAILED'}")
    print(f"Supabase: {'[SUCCESS] OK' if supabase_ok else '[FAIL] FAILED'}")
    print(f"Gemini AI: {'[SUCCESS] OK' if gemini_ok else '[FAIL] FAILED/SKIPPED'}")
    print("========================================")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
