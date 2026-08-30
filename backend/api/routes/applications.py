from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from core.database import get_db
from models.application import Application
from models.job import Job
from models.company import Company
from api.schemas import ApplicationOut, StatusUpdateRequest
from engine.application_service import log_status_change

router = APIRouter(prefix="/applications", tags=["Applications"])

# Full set of application statuses. The Kanban board treats the internal
# machine statuses ('pending', 'failed', 'needs_manual_action') as visible
# states so the user can always see and act on every application.
VALID_STATUSES = {
    "applied", "viewed", "responded", "interview", "offer", "rejected",
    "pending", "failed", "needs_manual_action",
}


@router.get("", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db)):
    apps = db.query(Application).order_by(Application.applied_at.desc()).all()
    result = []
    for a in apps:
        job = db.query(Job).filter(Job.id == a.job_id).first()
        comp = db.query(Company).filter(Company.id == job.company_id).first() if job else None
        result.append(ApplicationOut(
            id=a.id,
            job_id=a.job_id,
            job_title=job.title if job else "Unknown",
            company_name=comp.name if comp else "Unknown",
            resume_id=a.resume_id,
            applied_at=a.applied_at,
            method=a.method,
            status=a.status,
            cover_letter=a.cover_letter,
            notes=a.notes,
            job_url=job.url if job else None,
        ))
    return result


class NotesUpdateRequest(BaseModel):
    notes: str


@router.patch("/{app_id}/notes", response_model=ApplicationOut)
def update_notes(app_id: int, req: NotesUpdateRequest, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(404, "Application not found")
    app.notes = req.notes
    db.commit()
    db.refresh(app)

    job = db.query(Job).filter(Job.id == app.job_id).first()
    comp = db.query(Company).filter(Company.id == job.company_id).first() if job else None
    return ApplicationOut(
        id=app.id,
        job_id=app.job_id,
        job_title=job.title if job else "Unknown",
        company_name=comp.name if comp else "Unknown",
        resume_id=app.resume_id,
        applied_at=app.applied_at,
        method=app.method,
        status=app.status,
        cover_letter=app.cover_letter,
        notes=app.notes,
        job_url=job.url if job else None,
    )


@router.patch("/{app_id}/status", response_model=ApplicationOut)
def update_status(app_id: int, req: StatusUpdateRequest, db: Session = Depends(get_db)):
    if req.status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {VALID_STATUSES}")

    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(404, "Application not found")

    old_status = app.status
    app.status = req.status
    log_status_change(db, app.id, old_status, req.status, trigger_type="manual")
    db.commit()
    db.refresh(app)

    job = db.query(Job).filter(Job.id == app.job_id).first()
    comp = db.query(Company).filter(Company.id == job.company_id).first() if job else None

    return ApplicationOut(
        id=app.id,
        job_id=app.job_id,
        job_title=job.title if job else "Unknown",
        company_name=comp.name if comp else "Unknown",
        resume_id=app.resume_id,
        applied_at=app.applied_at,
        method=app.method,
        status=app.status,
        cover_letter=app.cover_letter,
        notes=app.notes,
        job_url=job.url if job else None,
    )