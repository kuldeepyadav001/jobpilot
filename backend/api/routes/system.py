"""System health / monitoring endpoint.

Aggregates the state of every component the dashboard's Monitoring page needs:
DB reachability, Ollama reachability, scheduler status, last pipeline run,
portal cookie configuration, uptime, and headline data counts.

This is the single source the frontend Monitoring page polls.
"""
import time
import os
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from core.config import settings
from models.job import Job
from models.application import Application
from models.response import Response
from models.resume import Resume
from scheduler.scheduler import scheduler
from api.routes.pipeline import _run_state

router = APIRouter(prefix="/system", tags=["System"])

_STARTED_AT = time.time()


class ComponentStatus(BaseModel):
    ok: bool
    detail: str


class SystemHealth(BaseModel):
    uptime_seconds: int
    db: ComponentStatus
    ollama: ComponentStatus
    scheduler: ComponentStatus
    pipeline: ComponentStatus
    cookies: dict
    counts: dict


def _cookie_status(name: str) -> str:
    val = os.getenv(name, "") or ""
    if not val:
        return "missing"
    if len(val) < 50:
        return "empty"
    return "configured"


async def _check_ollama() -> ComponentStatus:
    url = settings.ollama_base_url.rstrip("/") + "/api/tags"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url)
        if r.status_code == 200:
            return ComponentStatus(ok=True, detail=f"Reachable at {settings.ollama_base_url}")
        return ComponentStatus(ok=False, detail=f"Ollama HTTP {r.status_code}")
    except Exception as e:
        return ComponentStatus(ok=False, detail=f"Unreachable ({type(e).__name__})")


@router.get("/health", response_model=SystemHealth)
async def system_health(db: Session = Depends(get_db)):
    # DB check
    try:
        db.execute(func.now())
        db_status = ComponentStatus(ok=True, detail="Connected")
    except Exception as e:
        db_status = ComponentStatus(ok=False, detail=f"DB error: {type(e).__name__}")

    ollama_status = await _check_ollama()

    try:
        sched_running = scheduler.running
    except Exception:
        sched_running = False
    scheduler_status = ComponentStatus(
        ok=sched_running,
        detail=f"APScheduler {'running' if sched_running else 'not running'} (every {settings.scheduler_interval_hours}h)",
    )

    pipeline_status = ComponentStatus(
        ok=not _run_state["running"],
        detail=(
            f"{_run_state['status']}: {_run_state['message']}"
            if _run_state.get("started_at")
            else "No manual run yet this process"
        ),
    )

    cookies = {
        "internshala": _cookie_status("INTERNSHALA_COOKIE"),
        "naukri": _cookie_status("NAUKRI_COOKIE"),
    }

    counts = {
        "total_jobs": db.query(Job).count(),
        "total_applications": db.query(Application).count(),
        "total_responses": db.query(Response).count(),
        "total_resumes": db.query(Resume).count(),
        "interviews": db.query(Application).filter(Application.status == "interview").count(),
        "offers": db.query(Application).filter(Application.status == "offer").count(),
        "rejected": db.query(Application).filter(Application.status == "rejected").count(),
    }

    return SystemHealth(
        uptime_seconds=int(time.time() - _STARTED_AT),
        db=db_status,
        ollama=ollama_status,
        scheduler=scheduler_status,
        pipeline=pipeline_status,
        cookies=cookies,
        counts=counts,
    )
