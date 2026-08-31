import os
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger
from models.job import Job
from models.resume import Resume
from models.application import Application
from models.status_history import StatusHistory
from models.apply_log import ApplyLog
from engine.email_sender import send_job_application_email
from core.config import settings

# Daily real-apply cap per portal (config-driven so you can raise it to apply more).
MAX_DAILY_APPLIES = settings.daily_apply_cap


def log_status_change(db: Session, app_id: int, old: str, new: str, trigger_type: str = "auto"):
    history_entry = StatusHistory(
        application_id=app_id,
        old_status=old,
        new_status=new,
        trigger=trigger_type
    )
    db.add(history_entry)


def get_daily_apply_count(db: Session, portal: str) -> int:
    """Returns how many applications were sent to this portal today."""
    today = date.today()
    count = (
        db.query(func.count(ApplyLog.id))
        .filter(ApplyLog.portal == portal)
        .filter(ApplyLog.applied_date == today)
        .scalar()
    )
    return count or 0


def can_apply_today(db: Session, portal: str) -> bool:
    """Checks if we haven't exceeded the daily apply cap for this portal."""
    count = get_daily_apply_count(db, portal)
    if count >= MAX_DAILY_APPLIES:
        logger.warning(f"[Rate Limit] Daily cap reached for {portal}: {count}/{MAX_DAILY_APPLIES}")
        return False
    return True


def record_apply(db: Session, portal: str, job_id: int, method: str):
    """Logs an application to the daily rate limit tracker."""
    log_entry = ApplyLog(
        portal=portal,
        job_id=job_id,
        method=method,
        applied_date=date.today()
    )
    db.add(log_entry)


async def execute_job_application(
    db: Session,
    job_id: int,
    resume_id: int,
    cover_letter: str,
    method: str = "auto",  # auto / email / portal / manual
    recipient_email: Optional[str] = None
) -> Optional[Application]:
    """
    Core engine coordinator with smart routing and rate limiting.
    Async function that awaits browser actions cleanly.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    resume = db.query(Resume).filter(Resume.id == resume_id).first()

    if not job or not resume:
        logger.error(f"[Apply Service] Invalid Job ID ({job_id}) or Resume ID ({resume_id}).")
        return None

    if job.is_applied:
        logger.warning(f"[Apply Service] Job '{job.title}' already applied.")
        return None

    # --- RATE LIMIT CHECK ---
    if not can_apply_today(db, job.portal):
        logger.warning(f"[Apply Service] Skipping '{job.title}' — daily cap reached for {job.portal}.")
        return None

    # --- SMART ROUTING (if method is 'auto') ---
    if method == "auto":
        from engine.apply import PlaywrightApplyEngine  # lazy: avoid importing Playwright otherwise
        engine = PlaywrightApplyEngine(headless=True)
        detected_method, detected_email = await engine.detect_apply_method(job.url, job.portal)
        method = detected_method
        if detected_email:
            recipient_email = detected_email
        logger.info(f"[Smart Route] Job '{job.title}' routed to: {method}")

    # --- MANUAL APPLY: Just flag it, don't actually apply ---
    if method == "manual":
        new_app = Application(
            job_id=job.id,
            resume_id=resume.id,
            method="manual",
            status="needs_manual_action",
            cover_letter=cover_letter
        )
        db.add(new_app)
        db.flush()
        job.is_applied = True
        log_status_change(db, new_app.id, "none", "needs_manual_action", "auto")
        # Manual flag is not a real submission — do NOT consume the daily budget.
        db.commit()
        logger.info(f"[Apply Service] Flagged for manual apply: '{job.title}'")
        return new_app

    # --- CREATE APPLICATION RECORD ---
    new_app = Application(
        job_id=job.id,
        resume_id=resume.id,
        method=method,
        status="pending",
        cover_letter=cover_letter
    )
    db.add(new_app)
    db.flush()

    final_status = "pending"

    # --- ROUTE A: Email Apply ---
    if method == "email":
        if not recipient_email:
            logger.error("[Apply Service] No recipient email for email route.")
            final_status = "failed"
        else:
            success = send_job_application_email(
                to_email=recipient_email,
                subject=f"Application - {job.title}",
                body_text=cover_letter,
                resume_path=resume.file_path,
                resume_name=os.path.basename(resume.file_path)
            )
            final_status = "applied" if success else "failed"

    # --- ROUTE B: Portal Apply ---
    elif method == "portal":
        if job.portal == "internshala":
            from engine.apply import PlaywrightApplyEngine
            engine = PlaywrightApplyEngine(headless=True)
            final_status = await engine.apply_to_internshala(job.url, cover_letter)
        elif job.portal == "naukri":
            from engine.apply import PlaywrightApplyEngine
            engine = PlaywrightApplyEngine(headless=True)
            final_status = await engine.apply_to_naukri(job.url, cover_letter)
        else:
            # Freshersworld & other scraped portals: they have no stable in-portal
            # Easy Apply we can auto-submit, so never pretend. Applications on these
            # go through the email/external route; if a portal button is detected
            # without a supported auto-submit path, hand off honestly.
            logger.info(f"[Apply Service] Portal '{job.portal}' has no supported auto-submit; "
                        f"routing to manual action (never falsely applied).")
            final_status = "needs_manual_action"

    # --- COMMIT STATE ---
    new_app.status = final_status
    # Mark the job as handled for any terminal routing so it is never re-attempted
    # by the auto-apply step (no duplicate 'Needs Action' cards per cycle).
    job.is_applied = final_status in ("applied", "needs_manual_action")
    log_status_change(db, new_app.id, "none", final_status, "auto")

    # Daily apply BUDGET is only consumed by a real submission. 'needs_manual_action'
    # jobs did not actually submit anything, so they must not burn a slot.
    if final_status == "applied":
        record_apply(db, job.portal, job.id, method)

    db.commit()
    logger.info(f"[Apply Service] Application completed. Status: {final_status}")
    return new_app