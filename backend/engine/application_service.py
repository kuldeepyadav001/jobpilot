import os
import asyncio
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger
from models.job import Job
from models.resume import Resume
from models.application import Application
from models.status_history import StatusHistory
from engine.email_sender import send_job_application_email
from engine.apply import PlaywrightApplyEngine


def log_status_change(db: Session, app_id: int, old: str, new: str, trigger_type: str = "auto"):
    """Inserts status tracking snapshots to maintain auditing logs."""
    history_entry = StatusHistory(
        application_id=app_id,
        old_status=old,
        new_status=new,
        trigger=trigger_type
    )
    db.add(history_entry)


def execute_job_application(
    db: Session,
    job_id: int,
    resume_id: int,
    cover_letter: str,
    method: str = "portal",  # email / portal
    recipient_email: Optional[str] = None
) -> Optional[Application]:
    """
    Core engine coordinator. Executes the apply routing strategy, updates DB rows, 
    and handles automatic state promotion transitions.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    resume = db.query(Resume).filter(Resume.id == resume_id).first()

    if not job or not resume:
        logger.error(f"[Apply Service] Invalid Job ID ({job_id}) or Resume ID ({resume_id}).")
        return None

    if job.is_applied:
        logger.warning(f"[Apply Service] Job '{job.title}' was already targeted for application.")
        return None

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

    # ROUTE A: Email Apply Method
    if method == "email":
        if not recipient_email:
            logger.error("[Apply Service] Recipient target email missing.")
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

    # ROUTE B: Portal Automation Method
    else:
        if job.portal == "internshala":
            engine = PlaywrightApplyEngine(headless=True)
            final_status = asyncio.run(engine.apply_to_internshala(job.url, cover_letter))
        else:
            logger.warning(f"[Apply Service] Portal {job.portal} apply not automated in v1. Marking as manual action required.")
            final_status = "needs_manual_action"

    # Commit structural state records
    new_app.status = final_status
    job.is_applied = True if final_status == "applied" else False
    log_status_change(db, new_app.id, "none", final_status, "auto")

    db.commit()
    logger.info(f"[Apply Service] Application completed. Status: {final_status}")
    return new_app