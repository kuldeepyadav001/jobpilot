from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from models.job import Job
from models.application import Application
from models.analytics import AnalyticsSnapshot
from api.schemas import DashboardStats, SnapshotOut

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_jobs = db.query(Job).count()
    total_applied = db.query(Application).count()
    total_interviews = db.query(Application).filter(Application.status == "interview").count()
    total_rejected = db.query(Application).filter(Application.status == "rejected").count()

    avg_score = db.query(func.avg(Job.match_score)).scalar()

    # Portal breakdown
    portal_rows = (
        db.query(Job.portal, func.count(Job.id))
        .group_by(Job.portal)
        .all()
    )
    portal_breakdown = {row[0]: row[1] for row in portal_rows}

    return DashboardStats(
        total_jobs=total_jobs,
        total_applied=total_applied,
        total_interviews=total_interviews,
        total_rejected=total_rejected,
        avg_match_score=round(float(avg_score), 2) if avg_score else 0.0,
        portal_breakdown=portal_breakdown,
    )


@router.get("/snapshots", response_model=list[SnapshotOut])
def get_snapshots(db: Session = Depends(get_db)):
    return (
        db.query(AnalyticsSnapshot)
        .order_by(AnalyticsSnapshot.date.desc())
        .limit(30)
        .all()
    )