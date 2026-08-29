from datetime import date
from sqlalchemy.orm import Session
from loguru import logger
from core.database import SessionLocal
from core.config import settings
from scrapers.service import run_all_scrapers
from engine.service import score_unmatched_jobs
from engine.application_service import execute_job_application
from engine.email_tracker import scan_inbox
from ai.cover_letter import generate_tailored_cover_letter
from models.job import Job
from models.resume import Resume
from models.company import Company
from models.analytics import AnalyticsSnapshot
from engine.application_service import execute_job_application, can_apply_today

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


async def run_daily_automation_pipeline():
    logger.info("[Pipeline] Starting job automation pipeline cycle...")
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
        logger.info("[Pipeline] Step 3/5: Evaluating qualified jobs for application...")
        active_resume = db.query(Resume).filter(Resume.is_active == True).first()
        
        if not active_resume:
            logger.warning("[Pipeline] Apply step skipped: No active resume found.")
        else:
            qualified_jobs = (
                db.query(Job)
                .filter(Job.is_applied == False)
                .filter(Job.is_blacklisted == False)
                .filter(Job.match_score >= settings.match_score_threshold)
                .order_by(Job.match_score.desc())
                .limit(10)
                .all()
            )

            logger.info(f"[Pipeline] Found {len(qualified_jobs)} qualified jobs.")
            for job in qualified_jobs:
                # Check rate limit before each apply
                if not can_apply_today(db, job.portal):
                    logger.info(f"[Pipeline] Rate limit reached for {job.portal}. Stopping apply loop.")
                    break

                logger.info(f"[Pipeline] Applying to: '{job.title}' (Match: {job.match_score}%)")
                cover_letter = await generate_cover_letter_for_job(db, job, active_resume)
                
                await execute_job_application(
                    db=db,
                    job_id=job.id,
                    resume_id=active_resume.id,
                    cover_letter=cover_letter,
                    method="auto"  # Smart routing decides email/portal/manual
                )

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