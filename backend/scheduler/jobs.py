from datetime import date
from sqlalchemy.orm import Session
from loguru import logger
from core.database import SessionLocal
from core.config import settings
from scrapers.service import run_all_scrapers
from engine.service import score_unmatched_jobs
from engine.matcher import select_best_resume
from engine.application_service import execute_job_application
from engine.email_tracker import scan_inbox
from ai.cover_letter import generate_tailored_cover_letter
from models.job import Job
from models.resume import Resume
from models.company import Company
from models.analytics import AnalyticsSnapshot
from engine.application_service import can_apply_today

def select_apply_targets(db: Session, threshold: int, target_count: int) -> list[Job]:
    """Returns the top-N non-applied, non-blacklisted, scored jobs for applying.

    Selection is TOP-N by match score (robust while the score scale is
    uncalibrated). `threshold` acts as an optional soft floor: if > 0, jobs scoring
    below it are excluded; if 0, the floor is disabled.
    """
    q = (
        db.query(Job)
        .filter(Job.is_applied == False)
        .filter(Job.is_blacklisted == False)
        .filter(Job.match_score.isnot(None))
    )
    if threshold > 0:
        q = q.filter(Job.match_score >= threshold)

    return (
        q
        .order_by(Job.match_score.desc())
        .limit(max(1, target_count))
        .all()
    )


async def _run_apply_step(db: Session):
    """Selects qualified, non-applied, non-blacklisted jobs and applies to each
    using the best-matching resume. Respects the daily per-portal rate cap."""
    active_resumes = db.query(Resume).filter(Resume.is_active == True).all()
    if not active_resumes:
        logger.warning("[Pipeline] Apply step skipped: No active resume found.")
        return

    qualified_jobs = select_apply_targets(db, settings.match_score_threshold, settings.apply_target_count)
    logger.info(f"[Pipeline] Found {len(qualified_jobs)} qualified jobs with {len(active_resumes)} active resume(s) "
                f"(target={settings.apply_target_count}, floor={settings.match_score_threshold}).")
    for job in qualified_jobs:
        if not can_apply_today(db, job.portal):
            logger.info(f"[Pipeline] Rate limit reached for {job.portal}. Stopping apply loop.")
            break

        # Pick the single BEST resume for THIS job (auto-pick best resume).
        jd_text = f"{job.title} {job.description or ''}"
        best_resume, best_score = select_best_resume(jd_text, active_resumes)
        if best_resume is None:
            logger.warning(f"[Pipeline] No best resume could be selected for '{job.title}'. Skipping.")
            continue

        logger.info(f"[Pipeline] Applying to: '{job.title}' (Match: {job.match_score}%) "
                    f"| Best resume: '{best_resume.name}' (score {best_score:.2f})")
        cover_letter = await generate_cover_letter_for_job(db, job, best_resume)

        await execute_job_application(
            db=db,
            job_id=job.id,
            resume_id=best_resume.id,
            cover_letter=cover_letter,
            method="auto"  # Smart routing decides email/portal/manual
        )


async def generate_cover_letter_for_job(db: Session, job: Job, resume: Resume) -> str:
    company = db.query(Company).filter(Company.id == job.company_id).first()
    company_name = company.name if company else "Hiring Team"
    
    try:
        return await generate_tailored_cover_letter(
            job_title=job.title,
            company_name=company_name,
            job_description=job.description or job.title,
            resume_text=resume.parsed_text or ""
        )
    except Exception as e:
        logger.error(f"[Pipeline] LLM failed to generate cover letter: {e}")
        return "Please find attached my resume for your consideration."


async def run_daily_automation_pipeline(apply: bool | None = None):
    """Runs one full cycle.

    Args:
        apply:
          - True  (manual trigger)  -> also SUBMITS applications (if apply_mode='real').
          - False (scheduled)       -> scrape + score + track only; never applies.
          - None  -> fall back to settings.auto_apply for the scheduled path.

    This is the APPLY GATE: the risky submit step only ever runs when the caller
    explicitly requests it (i.e. your manual button click), never on a timer.
    """
    if apply is None:
        apply = settings.auto_apply
    logger.info(f"[Pipeline] Starting job automation pipeline cycle (apply={'ON' if apply else 'OFF'})...")
    db = SessionLocal()
    try:
        # Parse SEARCH_KEYWORDS from Settings
        kw_list = [k.strip() for k in settings.search_keywords.split(",") if k.strip()]
        if not kw_list:
            kw_list = ["python developer"]

        # STEP 1: Scrape Jobs for all keywords
        logger.info(f"[Pipeline] Step 1/5: Running scrapers for keywords {kw_list}...")
        scrape_stats = await run_all_scrapers(db, keywords=kw_list, location="remote", max_per_portal=5)
        logger.info(f"[Pipeline] Scraped jobs statistics: {scrape_stats}")

        # STEP 2: Score Jobs
        logger.info("[Pipeline] Step 2/5: Scoring new listings...")
        scored_count = score_unmatched_jobs(db)
        logger.info(f"[Pipeline] Scored {scored_count} new listings.")

        # STEP 3: Auto-Apply Engine (with Smart Routing + Rate Limiting)
        # APPLY GATE: skipped entirely on scheduled runs unless the user enabled AUTO_APPLY.
        if not apply:
            logger.info("[Pipeline] Step 3/5: APPLY GATE — automatic run does not apply. Skipping apply step.")
        else:
            await _run_apply_step(db)
        # STEP 4: Scan Recruiter Response Emails
        logger.info("[Pipeline] Step 4/5: Syncing recruiter email responses via IMAP...")
        email_count = scan_inbox(db, max_emails=10)
        logger.info(f"[Pipeline] Scanned {email_count} emails.")

        # STEP 5: Record Daily Snapshot
        logger.info("[Pipeline] Step 5/5: Generating daily progress analytics snapshot...")
        today = date.today()
        from models.application import Application
        total_applied = db.query(Application).count()
        total_interviews = db.query(Application).filter(Application.status == "interview").count()
        total_rejected = db.query(Application).filter(Application.status == "rejected").count()

        snapshot = db.query(AnalyticsSnapshot).filter(AnalyticsSnapshot.date == today).first()
        if not snapshot:
            snapshot = AnalyticsSnapshot(date=today)
            db.add(snapshot)
        
        snapshot.total_applied = total_applied
        snapshot.total_responses = total_interviews + total_rejected
        snapshot.total_interviews = total_interviews
        db.commit()
        logger.info("[Pipeline] Snapshot successfully updated.")

    except Exception as e:
        logger.exception(f"[Pipeline] Fatal error during automation cycle: {e}")
        db.rollback()
    finally:
        db.close()
        logger.info("[Pipeline] Pipeline cycle completed.")