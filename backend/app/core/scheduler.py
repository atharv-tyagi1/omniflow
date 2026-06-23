import asyncio
import logging
from backend.app.core.database import AsyncSessionLocal
from backend.app.services.outreach_service import OutreachService

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    _task = None
    _intel_task = None
    _maintenance_task = None
    _public_async_task = None
    _business_analyst_task = None
    _stop_event = None

    @classmethod
    async def start(cls, interval_seconds: int = 3600, intel_interval_seconds: int = 30, maintenance_interval_seconds: int = 86400, public_async_interval_seconds: int = 10, analyst_interval_seconds: int = 3600):
        """Start background schedulers for outreach and intel processing."""
        if cls._task is not None:
            return

        cls._stop_event = asyncio.Event()
        cls._task = asyncio.create_task(cls._run_outreach_loop(interval_seconds))
        cls._intel_task = asyncio.create_task(cls._run_intel_loop(intel_interval_seconds))
        cls._maintenance_task = asyncio.create_task(cls._run_maintenance_loop(maintenance_interval_seconds))
        cls._public_async_task = asyncio.create_task(cls._run_public_async_loop(public_async_interval_seconds))
        cls._business_analyst_task = asyncio.create_task(cls._run_business_analyst_loop(analyst_interval_seconds))
        logger.info(
            f"[Scheduler] Background schedulers started "
            f"(outreach: {interval_seconds}s, intel: {intel_interval_seconds}s, maintenance: {maintenance_interval_seconds}s, public_async: {public_async_interval_seconds}s, analyst: {analyst_interval_seconds}s)"
        )
        print(
            f"[Scheduler] Background schedulers started "
            f"(outreach: {interval_seconds}s, intel: {intel_interval_seconds}s, maintenance: {maintenance_interval_seconds}s, public_async: {public_async_interval_seconds}s)"
        )

    @classmethod
    async def stop(cls):
        """Stop all background schedulers."""
        if cls._stop_event:
            cls._stop_event.set()
        if cls._task:
            await cls._task
            cls._task = None
        if cls._intel_task:
            await cls._intel_task
            cls._intel_task = None
        if cls._maintenance_task:
            await cls._maintenance_task
            cls._maintenance_task = None
        if cls._public_async_task:
            await cls._public_async_task
            cls._public_async_task = None
        if cls._business_analyst_task:
            await cls._business_analyst_task
            cls._business_analyst_task = None
        logger.info("[Scheduler] Background schedulers stopped")
        print("[Scheduler] Background schedulers stopped")

    @classmethod
    async def _run_outreach_loop(cls, interval_seconds: int):
        """Original outreach evaluation loop — unchanged from Phase 7."""
        await asyncio.sleep(10)

        while not cls._stop_event.is_set():
            try:
                async with AsyncSessionLocal() as session:
                    await OutreachService.evaluate_triggers(session)
            except Exception as e:
                logger.error(f"[Scheduler] Error during outreach evaluation: {e}")

            try:
                await asyncio.wait_for(cls._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                continue

    @classmethod
    async def _run_intel_loop(cls, interval_seconds: int):
        """Intel worker polling loop — Phase 13.
        
        Polls the analytics_outbox for CONVERSATION_INTEL_PENDING events
        and processes them via IntelWorker. Runs on a faster cadence
        than the outreach loop (default: 30s).
        """
        # Delay initial run to let the app fully start
        await asyncio.sleep(15)

        while not cls._stop_event.is_set():
            try:
                from backend.app.services.intel.worker import IntelWorker
                async with AsyncSessionLocal() as session:
                    processed = await IntelWorker.process_outbox_batch(session)
                    if processed > 0:
                        logger.info(
                            "Operational Metric: Intel batch processed",
                            extra={
                                "metric_name": "intel_batch_processed",
                                "processed_count": processed,
                            }
                        )
            except Exception as e:
                logger.error(f"[Scheduler] Error during intel worker processing: {e}")

            try:
                await asyncio.wait_for(cls._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                continue

    @classmethod
    async def _run_maintenance_loop(cls, interval_seconds: int):
        """Runs daily maintenance tasks (e.g. idempotency cleanup)."""
        await asyncio.sleep(60) # delay initial run

        while not cls._stop_event.is_set():
            try:
                from backend.app.services.public.idempotency_service import IdempotencyService
                async with AsyncSessionLocal() as session:
                    await IdempotencyService.cleanup_expired_keys(session)
                    await IdempotencyService.cleanup_expired_async_jobs(session)
            except Exception as e:
                logger.error(f"[Scheduler] Error during maintenance processing: {e}")

            try:
                await asyncio.wait_for(cls._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                continue

    @classmethod
    async def _run_public_async_loop(cls, interval_seconds: int):
        """Runs the public async job worker loop."""
        await asyncio.sleep(20) # delay initial run

        while not cls._stop_event.is_set():
            try:
                from backend.app.services.public.async_job_worker import PublicAsyncJobWorker
                async with AsyncSessionLocal() as session:
                    await PublicAsyncJobWorker.process_pending_jobs(session)
            except Exception as e:
                logger.error(f"[Scheduler] Error during public async job processing: {e}")

            try:
                await asyncio.wait_for(cls._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                continue

    @classmethod
    async def _run_business_analyst_loop(cls, interval_seconds: int):
        """Runs the Business Analyst insight and reporting loop."""
        await asyncio.sleep(45) # delay initial run

        while not cls._stop_event.is_set():
            try:
                from sqlalchemy import text
                from backend.app.models.workspace import Workspace
                from sqlalchemy.future import select
                from backend.app.services.business.insight_engine import InsightEngine
                from backend.app.services.business.executive_summary_service import ExecutiveSummaryService
                from backend.app.services.business.recommendation_engine import RecommendationEngine
                from backend.app.core.telemetry import log_business_telemetry

                async with AsyncSessionLocal() as session:
                    # 1. Advisory Lock for safety (only on Postgres)
                    from backend.app.core.database import engine
                    is_postgres = engine.dialect.name == "postgresql"
                    
                    locked = True
                    if is_postgres:
                        lock_result = await session.execute(text("SELECT pg_try_advisory_lock(14000)"))
                        locked = lock_result.scalar()
                    
                    if locked:
                        log_business_telemetry("scheduler_lock_acquired", workspace_id="system")
                        try:
                            # 2. Timeout protection for the whole loop
                            async def run_analyst():
                                workspaces = await session.execute(select(Workspace))
                                for ws in workspaces.scalars().all():
                                    insight_engine = InsightEngine(session)
                                    # Generate insights deterministically
                                    insights = await insight_engine.generate_insights(str(ws.id))
                                    
                                    if insights:
                                        # Generate recommendations
                                        rec_engine = RecommendationEngine(session)
                                        await rec_engine.generate_recommendations(str(ws.id), [i.id for i in insights])
                                    
                                    # Generate Executive Report (weekly)
                                    exec_service = ExecutiveSummaryService(session)
                                    import datetime
                                    current_week_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-W%W")
                                    await exec_service.generate_report(str(ws.id), "weekly", current_week_str)
                            
                            # Timeout to prevent hanging DB connections
                            await asyncio.wait_for(run_analyst(), timeout=300)
                            
                        finally:
                            if is_postgres:
                                await session.execute(text("SELECT pg_advisory_unlock(14000)"))
                            await session.commit()
                    else:
                        log_business_telemetry("scheduler_lock_denied", workspace_id="system")
                            
            except asyncio.TimeoutError:
                logger.error("[Scheduler] Business Analyst generation timed out.")
                from backend.app.core.telemetry import log_business_telemetry
                log_business_telemetry("insight_generation_timeout", workspace_id="system")
            except Exception as e:
                logger.error(f"[Scheduler] Error during business analyst processing: {e}")
                from backend.app.core.telemetry import log_business_telemetry
                log_business_telemetry("insight_generation_failure", workspace_id="system", details={"error": str(e)})

            try:
                await asyncio.wait_for(cls._stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                continue

