import asyncio
from backend.app.core.database import async_session_maker
from backend.app.services.outreach_service import OutreachService


class BackgroundScheduler:
    _task = None
    _stop_event = None

    @classmethod
    async def start(cls, interval_seconds: int = 3600):
        """Start the background scheduler to evaluate triggers periodically."""
        if cls._task is not None:
            return

        cls._stop_event = asyncio.Event()
        cls._task = asyncio.create_task(cls._run_loop(interval_seconds))
        print(
            f"[Scheduler] Background proactive outreach scheduler started (interval: {interval_seconds}s)"
        )

    @classmethod
    async def stop(cls):
        """Stop the background scheduler."""
        if cls._stop_event:
            cls._stop_event.set()
        if cls._task:
            await cls._task
            cls._task = None
        print("[Scheduler] Background proactive outreach scheduler stopped")

    @classmethod
    async def _run_loop(cls, interval_seconds: int):
        # We start with an initial sleep so it doesn't block startup
        await asyncio.sleep(10)

        while not cls._stop_event.is_set():
            try:
                # Provide a new DB session for each evaluation cycle
                async with async_session_maker() as session:
                    await OutreachService.evaluate_triggers(session)
            except Exception as e:
                print(f"[Scheduler] Error during outreach evaluation: {e}")

            # Wait for the interval, but allow interrupting via stop_event
            try:
                await asyncio.wait_for(cls._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                # Timeout is expected, it means we should run again
                pass
