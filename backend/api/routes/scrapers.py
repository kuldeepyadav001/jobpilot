"""Scraper diagnostic + control endpoints (single-user local tool).

DRY-RUN: scrapes the live portals but saves nothing, so you can validate the
scrapers before trusting the pipeline. Because scraping opens a headless browser
and can take minutes, it runs in the BACKGROUND (mirroring the pipeline trigger)
so the HTTP request never times out — polls GET /status for progress.
"""
import asyncio
import threading
import time

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from core.config import settings
from scrapers.service import scrape_diagnostics

router = APIRouter(prefix="/scrapers", tags=["Scrapers"])

# In-memory, single-run tracker (single-user local tool; matches pipeline trigger).
_run_lock = threading.Lock()
_state = {
    "running": False,
    "status": "idle",           # idle | running | success | error
    "message": "No run yet.",
    "keywords": [],
    "location": None,
    "max_per_portal": None,
    "results": [],
    "started_at": None,
    "completed_at": None,
}


class DiagStart(BaseModel):
    started: bool
    message: str


class DiagStatus(BaseModel):
    running: bool
    status: str
    message: str
    keywords: List[str]
    location: Optional[str]
    max_per_portal: Optional[int]
    results: List[dict]


async def _background_diag(keywords: List[str], location: str, max_per_portal: int):
    global _state
    try:
        report = await scrape_diagnostics(keywords, location, max_per_portal)
        _state["results"] = report["results"]
        _state["status"] = "success"
        _state["message"] = "Dry-run scrape complete."
    except Exception as e:  # noqa: BLE001
        _state["status"] = "error"
        _state["message"] = f"{type(e).__name__}: {e}"
    finally:
        _state["running"] = False
        _state["completed_at"] = time.time()


@router.post("/diagnostics", response_model=DiagStart)
async def start_diagnostics(
    keywords: str = Query(None, description="Comma-separated keywords. Defaults to SEARCH_KEYWORDS."),
    location: str = Query(None),
    max_per_portal: int = Query(None, ge=1, le=30),
):
    """Starts a background dry-run scrape (saves nothing) and returns immediately."""
    with _run_lock:
        if _state["running"]:
            raise HTTPException(409, "A diagnostic scrape is already in progress.")

        kw_list = _resolve_keywords(keywords)
        env_location = location or settings.search_location
        mpp = max_per_portal or settings.max_per_portal

        _state.update({
            "running": True,
            "status": "running",
            "message": "Dry-run scrape started.",
            "keywords": kw_list,
            "location": env_location,
            "max_per_portal": mpp,
            "results": [],
            "started_at": time.time(),
            "completed_at": None,
        })
        asyncio.create_task(_background_diag(kw_list, env_location, mpp))

    return DiagStart(started=True, message="Dry-run scrape started in background.")


@router.get("/diagnostics/status", response_model=DiagStatus)
def diagnostics_status():
    return DiagStatus(
        running=_state["running"],
        status=_state["status"],
        message=_state["message"],
        keywords=_state["keywords"],
        location=_state["location"],
        max_per_portal=_state["max_per_portal"],
        results=_state["results"],
    )


class SessionCheck(BaseModel):
    portal: str
    ok: bool
    logged_in: bool
    message: str


async def _check_session(portal: str) -> SessionCheck:
    """Loads the portal in a headless browser with the configured cookie and checks
    whether we are actually logged in. This is the REAL cookie validity test (the
    settings page only measures the cookie string length, which proves nothing)."""
    import os
    from scrapers.base import BaseBrowser

    if portal == "naukri":
        start_url = "https://www.naukri.com/"
        cookie_env = os.getenv("NAUKRI_COOKIE", "")
        domain = ".naukri.com"
    else:
        start_url = "https://internshala.com/internships"
        cookie_env = os.getenv("INTERNSHALA_COOKIE", "")
        domain = ".internshala.com"

    if not cookie_env:
        return SessionCheck(portal=portal, ok=False, logged_in=False,
                            message=f"No {portal.upper()}_COOKIE set in .env.")

    browser = BaseBrowser(headless=True)
    try:
        page = await browser.init_browser(cookie_string=cookie_env, domain=domain)
        await page.goto(start_url, wait_until="domcontentloaded", timeout=45000)
        # check_session_valid inspects URL/logout text to decide if logged in.
        logged_in = await browser.check_session_valid(page, portal)
        msg = ("Logged in (cookie valid)." if logged_in
               else "NOT logged in — cookie likely expired. Refresh it in .env.")
        return SessionCheck(portal=portal, ok=logged_in, logged_in=logged_in, message=msg)
    except Exception as e:
        return SessionCheck(portal=portal, ok=False, logged_in=False,
                            message=f"Session check error: {type(e).__name__}: {e}")
    finally:
        await browser.close()


@router.get("/session-check", response_model=List[SessionCheck])
async def session_check(portal: str = Query("internshala")):
    """Verifies the configured cookie actually logs into the portal (real test)."""
    return [await _check_session(portal)]


def _resolve_keywords(keywords: Optional[str]) -> List[str]:
    if keywords and keywords.strip():
        return [k.strip() for k in keywords.split(",") if k.strip()]
    kv = [k.strip() for k in settings.search_keywords.split(",") if k.strip()]
    return kv or ["python developer"]
