import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from loguru import logger
from core.config import settings
from scheduler.jobs import run_daily_automation_pipeline
from engine.maintenance import cleanup_stale_jobs
from core.database import SessionLocal

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
    """Wrapper to run the async job pipeline in a synchronous scheduler context thread.

    Uses settings.auto_apply so the scheduled run does NOT apply unless explicitly enabled —
    applying is triggered manually by the user (the APPLY GATE).
    """
    logger.info("[Scheduler] Executing scheduled pipeline task...")
    asyncio.run(run_daily_automation_pipeline(apply=settings.auto_apply))


def run_weekly_cleanup_wrapper():
    """Weekly housekeeping: prune stale, never-applied jobs."""
    logger.info("[Scheduler] Running weekly job cleanup...")
    db = SessionLocal()
    try:
        cleanup_stale_jobs(db)
    except Exception as e:
        logger.exception(f"[Scheduler] Weekly cleanup failed: {e}")
    finally:
        db.close()


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

    # 2. Weekly job cleanup (Sunday 03:00). Skips itself if disabled.
    scheduler.add_job(
        run_weekly_cleanup_wrapper,
        'cron',
        day_of_week='sun',
        hour=3,
        minute=0,
        id='weekly_job_cleanup'
    )

    scheduler.start()
    logger.info("[Scheduler] Engine started successfully.")


def shutdown_scheduler():
    """Shuts down background scheduling cleanly."""
    if scheduler.running:
        logger.info("[Scheduler] Shuttling down daemon tasks...")
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Engine terminated.")