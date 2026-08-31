import asyncio
import threading
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.schemas import PipelineResponse
from scheduler.jobs import run_daily_automation_pipeline
from scheduler.run_state import reset_run, finish_run, get_run_state

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# In-memory, single-run tracker for the manual pipeline trigger shared with the
# scheduler (see scheduler/run_state.py). Includes the current step + a heartbeat
# so the UI shows live progress while the slow scrape/enrich step runs.
_run_lock = threading.Lock()


class RunStatus(BaseModel):
    running: bool
    status: str
    message: str
    step: str | None = None
    last_activity_at: float | None = None


async def _background_run():
    try:
        # Manual trigger => apply=True => the full cycle INCLUDING applications runs.
        await run_daily_automation_pipeline(apply=True)
        finish_run("success", "Pipeline cycle completed.")
    except Exception as e:
        finish_run("error", str(e))


@router.post("/run", response_model=PipelineResponse)
async def trigger_pipeline():
    with _run_lock:
        if get_run_state()["running"]:
            raise HTTPException(409, "A pipeline run is already in progress.")

        reset_run(start=True)

        # Fire-and-forget on the event loop so the HTTP request returns immediately.
        asyncio.create_task(_background_run())

    return PipelineResponse(status="started", message="Pipeline cycle started in background.")


def status_payload() -> dict:
    """The pipeline run-state, augmented with a stale-detection heartbeat."""
    st = get_run_state()
    # Mark a run as stalled if we haven't heard from it in 10 minutes (it may be
    # hung on a slow network call, not silently making progress).
    if st["running"] and st.get("last_activity_at"):
        if time.time() - st["last_activity_at"] > 600:
            st["message"] = st["message"] + " (no update in 10 min — possibly stalled)"
    return st


@router.get("/status", response_model=RunStatus)
def pipeline_status():
    st = status_payload()
    return RunStatus(
        running=st["running"],
        status=st["status"],
        message=st["message"],
        step=st.get("step"),
        last_activity_at=st.get("last_activity_at"),
    )
