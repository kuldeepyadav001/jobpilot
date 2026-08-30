from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from models.job import Job
from models.company import Company
from api.schemas import JobOut, JobListResponse
from engine.maintenance import cleanup_stale_jobs

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.delete("/cleanup")
def run_cleanup(db: Session = Depends(get_db)):
    """Manually triggers the stale-job cleanup (also runs weekly on schedule)."""
    result = cleanup_stale_jobs(db, now=None)
    return {"status": "ok", **result}


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    portal: str = Query(None),
    min_score: float = Query(None),
    applied: bool = Query(None),
    search: str = Query(None),
    job_type: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Job).join(Company, Job.company_id == Company.id)

    if portal:
        query = query.filter(Job.portal == portal)
    if min_score is not None:
        query = query.filter(Job.match_score >= min_score)
    if applied is not None:
        query = query.filter(Job.is_applied == applied)
    if search:
        query = query.filter(Job.title.ilike(f"%{search}%"))
    if job_type:
        query = query.filter(Job.job_type == job_type)

    total = query.count()
    jobs = (
        query
        .order_by(Job.match_score.desc().nullslast(), Job.scraped_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for j in jobs:
        comp = db.query(Company).filter(Company.id == j.company_id).first()
        result.append(JobOut(
            id=j.id,
            portal=j.portal,
            title=j.title,
            company_name=comp.name if comp else "Unknown",
            location=j.location,
            salary_min=j.salary_min,
            salary_max=j.salary_max,
            description=j.description,
            url=j.url,
            job_type=j.job_type or "job",
            match_score=j.match_score,
            is_applied=j.is_applied,
            scraped_at=j.scraped_at,
        ))

    return JobListResponse(total=total, page=page, page_size=page_size, jobs=result)