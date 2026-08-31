"""In-memory pipeline run-state shared between the scheduler and the status API.

A single user, local tool: a dict is enough. Allows the pipeline to publish the
current step + a heartbeat so the UI shows live progress instead of a bare
"running" while it grinds through the slow scrape/enrich step.
"""
import threading
import time

_run_lock = threading.Lock()
_state = {
    "running": False,
    "status": "idle",           # idle | running | success | error
    "message": "No run yet.",
    "step": None,               # e.g. "Scraping keyword 3/10", "Scoring", "Applying"
    "started_at": None,
    "last_activity_at": None,
    "completed_at": None,
}


def reset_run(start: bool) -> None:
    with _run_lock:
        _state["running"] = start
        _state["status"] = "running" if start else "idle"
        _state["message"] = "Pipeline cycle started." if start else "No run yet."
        _state["step"] = None
        _state["started_at"] = time.time() if start else None
        _state["last_activity_at"] = time.time() if start else None
        _state["completed_at"] = None


def set_step(step: str) -> None:
    with _run_lock:
        _state["step"] = step
        _state["last_activity_at"] = time.time()
        _state["message"] = step


def heartbeat() -> None:
    with _run_lock:
        _state["last_activity_at"] = time.time()


def finish_run(status: str, message: str) -> None:
    with _run_lock:
        _state["running"] = False
        _state["status"] = status
        _state["message"] = message
        _state["completed_at"] = time.time()


def get_run_state() -> dict:
    with _run_lock:
        return dict(_state)
