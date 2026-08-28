from datetime import date
from sqlalchemy.orm import Session
from loguru import logger
from core.database import SessionLocal
from scrapers.service import run_all_scrapers
from engine.service import score_unmatched_jobs
from engine.application_service import execute_job_application
from engine.email_tracker import scan_inbox
from ai.cover_letter import generate_tailored_cover_letter
from models.job import Job
from models.resume import Resume
from models.company import Company
from models.analytics import AnalyticsSnapshot


async def generate_cover_letter_for_job(db: Session, job: Job, resume: Resume) -> str:
    """Helper to query the active company and request tailored cover letters."""
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
    """
    Executes the complete scheduled job automation cycle:
    1. Scrapes job listings
    2. Runs TF-IDF matching/scoring
    3. Auto-applies to qualified listings
    4. Scans email replies for status changes
    5. Records daily snapshot analytics
    """
    logger.info("[Pipeline] Starting job automation pipeline cycle...")
    db = SessionLocal()
    try:
        # STEP 1: Scrape Jobs
        logger.info("[Pipeline] Step 1/5: Running scrapers...")
        scrape_stats = await run_all_scrapers(db, keyword="python developer", location="remote", max_per_portal=10)
        logger.info(f"[Pipeline] Scraped jobs: {scrape_stats}")

        # STEP 2: Score Jobs
        logger.info("[Pipeline] Step 2/5: Scoring new listings...")
        scored_count = score_unmatched_jobs(db)
        logger.info(f"[Pipeline] Scored {scored_count} new listings.")

        # STEP 3: Auto-Apply Engine
        logger.info("[Pipeline] Step 3/5: Evaluating qualified jobs for application...")
        active_resume = db.query(Resume).filter(Resume.is_active == True).first()
        
        if not active_resume:
            logger.warning("[Pipeline] Apply step skipped: No active resume found in database.")
        else:
            # Query jobs above threshold (e.g. 10% for testing, defaults to settings value)
            qualified_jobs = (
                db.query(Job)
                .filter(Job.is_applied == False)
                .filter(Job.is_blacklisted == False)
                .filter(Job.match_score >= 10.0)  # low threshold for localized testing
                .order_by(Job.match_score.desc())
                .limit(3)  # Rate limit: Apply to at most 3 jobs per scheduler cycle to avoid spam limits
                .all()
            )

            logger.info(f"[Pipeline] Found {len(qualified_jobs)} qualified jobs matching criteria.")
            for job in qualified_jobs:
                logger.info(f"[Pipeline] Applying to job: '{job.title}' (Match: {job.match_score}%)")
                
                # Render cover letter
                cover_letter = await generate_cover_letter_for_job(db, job, active_resume)
                
                # Apply using playbooks (defaults to safe portal mock apply)
                execute_job_application(
                    db=db,
                    job_id=job.id,
                    resume_id=active_resume.id,
                    cover_letter=cover_letter,
                    method="portal"
                )

        # STEP 4: Scan Recruiter Response Emails
        logger.info("[Pipeline] Step 4/5: Syncing recruiter email responses via IMAP...")
        email_count = scan_inbox(db, max_emails=10)
        logger.info(f"[Pipeline] Scanned {email_count} emails.")

        # STEP 5: Record Daily Snapshot
        logger.info("[Pipeline] Step 5/5: Generating daily progress analytics snapshot...")
        today = date.today()
        # Compute stats
        from models.application import Application
        total_applied = db.query(Application).count()
        total_interviews = db.query(Application).filter(Application.status == "interview").count()
        total_rejected = db.query(Application).filter(Application.status == "rejected").count()

        # Update or create database daily analytics snapshot
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