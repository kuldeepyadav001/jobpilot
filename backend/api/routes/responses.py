from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.response import Response
from models.application import Application
from models.job import Job
from models.company import Company
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/responses", tags=["Responses"])


class ResponseOut(BaseModel):
    id: int
    application_id: int
    job_title: Optional[str]
    company_name: Optional[str]
    response_type: str
    received_at: Optional[datetime]
    parsed_summary: Optional[str]
    is_read: bool

    class Config:
        from_attributes = True


@router.get("", response_model=List[ResponseOut])
def list_responses(db: Session = Depends(get_db)):
    responses = db.query(Response).order_by(Response.received_at.desc()).all()
    result = []
    for r in responses:
        app = db.query(Application).filter(Application.id == r.application_id).first()
        job = db.query(Job).filter(Job.id == app.job_id).first() if app else None
        comp = db.query(Company).filter(Company.id == job.company_id).first() if job else None
        result.append(ResponseOut(
            id=r.id,
            application_id=r.application_id,
            job_title=job.title if job else "Unknown",
            company_name=comp.name if comp else "Unknown",
            response_type=r.response_type,
            received_at=r.received_at,
            parsed_summary=r.parsed_summary,
            is_read=r.is_read,
        ))
    return result


@router.post("/scan")
def trigger_email_scan(db: Session = Depends(get_db)):
    """Manually trigger IMAP inbox scan."""
    from engine.email_tracker import scan_inbox
    count = scan_inbox(db, max_emails=20)
    return {"status": "ok", "emails_processed": count}