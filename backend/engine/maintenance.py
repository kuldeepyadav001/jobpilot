"""Housekeeping: prune stale, never-applied jobs so the DB doesn't fill up."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from loguru import logger

from core.config import settings
from models.job import Job
from models.application import Application


def cleanup_stale_jobs(db: Session, retention_days: int | None = None, enabled: bool | None = None,
                       now: datetime | None = None) -> dict:
    """Deletes jobs that are older than `retention_days`, were never applied, and
    are not referenced by any application. Returns counts for reporting.

    - Applied jobs and jobs with an application record are always kept (they're "used").
    - `now` is injectable for deterministic tests.
    """
    enabled = settings.job_cleanup_enabled if enabled is None else enabled
    retention_days = settings.job_retention_days if retention_days is None else retention_days

    if not enabled:
        logger.info("[Cleanup] Job cleanup is disabled (JOB_CLEANUP_ENABLED=false). Skipping.")
        return {"enabled": False, "scanned": 0, "deleted": 0, "retention_days": retention_days}

    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)

    # Jobs considered: older than cutoff, not applied. (scraped_at may be NULL if
    # inserted directly; treat NULL as not-eligible so we never nuke fresh rows.)
    stale = (
        db.query(Job)
        .filter(Job.is_applied == False)
        .filter(Job.scraped_at.isnot(None))
        .filter(Job.scraped_at < cutoff)
        .all()
    )

    # Never delete a job that is referenced by an application.
    referenced_job_ids = {row for (row,) in db.query(Application.job_id).all()}
    to_delete = [j.id for j in stale if j.id not in referenced_job_ids]

    deleted = 0
    if to_delete:
        deleted = db.query(Job).filter(Job.id.in_(to_delete)).delete(synchronize_session=False)
        db.commit()
        logger.info(f"[Cleanup] Pruned {deleted} stale unapplied jobs (older than {retention_days}d).")
    else:
        logger.info(f"[Cleanup] No stale jobs to prune ({len(stale)} stale, all referenced).")

    return {"enabled": True, "scanned": len(stale), "deleted": deleted, "retention_days": retention_days}
