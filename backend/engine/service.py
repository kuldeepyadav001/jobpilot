from typing import List, Optional
from sqlalchemy.orm import Session
from loguru import logger
from models.resume import Resume
from models.job import Job
from engine.parser import parse_resume_file
from engine.matcher import select_best_resume, compute_hybrid_match_score


def register_resume(
    db: Session,
    name: str,
    file_path: str,
    file_type: str,
    tags: Optional[List[str]] = None,
    raw_text: Optional[str] = None
) -> Resume:
    """Extracts text, creates or updates a Resume entity in the DB."""
    parsed_text = raw_text or parse_resume_file(file_path, file_type)

    resume = Resume(
        name=name,
        file_path=file_path,
        file_type=file_type.lower().replace(".", ""),
        tags=tags or [],
        version=1,
        parsed_text=parsed_text,
        is_active=True
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    logger.info(f"Registered resume: '{name}' (ID: {resume.id}, Tags: {tags})")
    return resume


def score_unmatched_jobs(db: Session) -> int:
    """
    Scores all unscored jobs in the database against all active resumes using Hybrid matching.
    Updates Job.match_score with the highest score found.
    """
    active_resumes = db.query(Resume).filter(Resume.is_active == True).all()
    if not active_resumes:
        logger.warning("No active resumes found in database to score jobs.")
        return 0

    unscored_jobs = db.query(Job).filter(Job.match_score == None).all()
    scored_count = 0

    for job in unscored_jobs:
        jd_text = f"{job.title} {job.description or ''}"
        best_resume, score = select_best_resume(jd_text, active_resumes)
        job.match_score = score
        scored_count += 1

    db.commit()
    logger.info(f"Scored {scored_count} jobs using hybrid matching.")
    return scored_count