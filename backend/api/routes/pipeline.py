import asyncio
import threading
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.schemas import PipelineResponse
from scheduler.jobs import run_daily_automation_pipeline

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# In-memory, single-run tracker for the manual pipeline trigger.
# A real deployment would use the scheduler + a persistent run log; this is
# sufficient for a single-user local app and avoids racing the HTTP timeout.
_run_lock = threading.Lock()
_run_state = {
    "running": False,
    "status": "idle",           # idle | running | success | error
    "message": "No run yet.",
    "started_at": None,
    "completed_at": None,
}


class RunStatus(BaseModel):
    running: bool
    status: str
    message: str


async def _background_run():
    global _run_state
    try:
        # Manual trigger => apply=True => the full cycle INCLUDING applications runs.
        await run_daily_automation_pipeline(apply=True)
        _run_state["status"] = "success"
        _run_state["message"] = "Pipeline cycle completed."
    except Exception as e:
        _run_state["status"] = "error"
        _run_state["message"] = str(e)
    finally:
        _run_state["running"] = False
        _run_state["completed_at"] = time.time()


@router.post("/run", response_model=PipelineResponse)
async def trigger_pipeline():
    with _run_lock:
        if _run_state["running"]:
            raise HTTPException(409, "A pipeline run is already in progress.")

        _run_state["running"] = True
        _run_state["status"] = "running"
        _run_state["message"] = "Pipeline cycle started."
        _run_state["started_at"] = time.time()
        _run_state["completed_at"] = None

        # Fire-and-forget on the event loop so the HTTP request returns immediately.
        asyncio.create_task(_background_run())

    return PipelineResponse(status="started", message="Pipeline cycle started in background.")


@router.get("/status", response_model=RunStatus)
def pipeline_status():
    return RunStatus(
        running=_run_state["running"],
        status=_run_state["status"],
        message=_run_state["message"],
    )
