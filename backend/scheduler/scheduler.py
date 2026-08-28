import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from loguru import logger
from core.config import settings
from scheduler.jobs import run_daily_automation_pipeline

# Initialize background scheduler with a single execution thread to prevent database locks
executors = {
    'default': ThreadPoolExecutor(1)
}
job_defaults = {
    'coalesce': True,  # Merge missed executions into a single run
    'max_instances': 1  # Block overlapping instance executions
}

scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)


def run_pipeline_sync_wrapper():
    """Wrapper to run the async job pipeline in a synchronous scheduler context thread."""
    logger.info("[Scheduler] Executing scheduled pipeline task...")
    asyncio.run(run_daily_automation_pipeline())


def start_scheduler():
    """Starts the background scheduler daemon."""
    if scheduler.running:
        return

    logger.info(f"[Scheduler] Starting background engine (Interval: every {settings.scheduler_interval_hours} hours)")
    
    # 1. Add recurrent job pipeline
    scheduler.add_job(
        run_pipeline_sync_wrapper,
        'interval',
        hours=settings.scheduler_interval_hours,
        id='job_automation_pipeline'
    )
    
    scheduler.start()
    logger.info("[Scheduler] Engine started successfully.")


def shutdown_scheduler():
    """Shuts down background scheduling cleanly."""
    if scheduler.running:
        logger.info("[Scheduler] Shuttling down daemon tasks...")
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Engine terminated.")