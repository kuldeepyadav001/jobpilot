import sys
import time as _t
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

_STARTED_AT = _t.time()

from core.database import get_db
from models.job import Job
from models.application import Application

# Import all route modules (aliasing settings to avoid collision with config.settings)
from api.routes import (
    jobs,
    applications,
    resumes,
    analytics,
    pipeline,
    responses,
    system,
    settings as settings_route,
)
from scheduler.scheduler import start_scheduler, shutdown_scheduler

# 1. Logging Setup
logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
logger.add("logs/jobpilot.log", rotation="10 MB", retention="30 days", level="INFO")

# 2. FastAPI App Instantiation
app = FastAPI(
    title="JobPilot API",
    version="1.1.0",
    description="Automated job hunting system",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 3. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Register All API Routers (app is defined now)
app.include_router(jobs.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(resumes.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(responses.router, prefix="/api")
app.include_router(settings_route.router, prefix="/api")
app.include_router(system.router, prefix="/api")


# 5. Lifecycle Event Handlers
@app.on_event("startup")
def on_startup():
    logger.info("JobPilot API starting up...")
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    logger.info("JobPilot API shutting down...")
    shutdown_scheduler()


# 6. Core Endpoints
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "JobPilot API", "version": "1.1.0"}


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    """Prometheus exposition format metrics — scraped by the prometheus service."""
    import time as _t
    from models.response import Response
    from models.resume import Resume

    total_jobs = db.query(Job).count()
    total_apps = db.query(Application).count()
    interviews = db.query(Application).filter(Application.status == "interview").count()
    rejected = db.query(Application).filter(Application.status == "rejected").count()
    offers = db.query(Application).filter(Application.status == "offer").count()
    responses = db.query(Response).count()
    resumes = db.query(Resume).count()
    # Status funnel
    status_counts = {}
    for status, cnt in db.query(Application.status, func.count(Application.id)).group_by(Application.status).all():
        status_counts[status or "none"] = cnt

    def _g(name, value, help_):
        return [
            f"# HELP {name} {help_}",
            f"# TYPE {name} gauge",
            f"{name} {value}",
        ]

    lines = []
    lines += _g("jobpilot_jobs_total", total_jobs, "Total scraped jobs")
    lines += _g("jobpilot_applications_total", total_apps, "Total applications")
    lines += _g("jobpilot_interviews_total", interviews, "Interview invitations")
    lines += _g("jobpilot_offers_total", offers, "Offers received")
    lines += _g("jobpilot_rejected_total", rejected, "Rejected applications")
    lines += _g("jobpilot_responses_total", responses, "Recruiter responses detected")
    lines += _g("jobpilot_resumes_total", resumes, "Resumes uploaded")
    lines += _g("jobpilot_uptime_seconds", int(_t.time() - _STARTED_AT), "Process uptime in seconds")
    for status, cnt in status_counts.items():
        lines += _g(f"jobpilot_applications_status_{{status=\"{status}\"}}", cnt, f"Applications in status '{status}'")

    return Response("\n".join(lines), media_type="text/plain")


@app.get("/")
def root():
    return {"message": "JobPilot is running. Visit /docs for API documentation."}