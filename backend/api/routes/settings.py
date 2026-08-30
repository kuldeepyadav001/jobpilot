import os
from fastapi import APIRouter
from pydantic import BaseModel
from core.config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])


class CookieHealth(BaseModel):
    portal: str
    cookie_configured: bool
    cookie_length: int
    status: str  # "configured" | "missing" | "empty"


class AppSettings(BaseModel):
    apply_mode: str          # 'real' | 'dry_run'
    auto_apply: bool         # whether the scheduled run also applies
    candidate_name: str
    job_cleanup_enabled: bool
    job_retention_days: int


@router.get("/app", response_model=AppSettings)
def app_settings():
    """Returns non-secret application settings so the UI can warn about apply mode."""
    return AppSettings(
        apply_mode=settings.apply_mode,
        auto_apply=settings.auto_apply,
        candidate_name=settings.candidate_name,
        job_cleanup_enabled=settings.job_cleanup_enabled,
        job_retention_days=settings.job_retention_days,
    )


@router.get("/cookie-health", response_model=list[CookieHealth])
def check_cookie_health():
    """Returns the status of portal session cookies."""
    portals = [
        {"name": "internshala", "env_key": "INTERNSHALA_COOKIE"},
        {"name": "naukri", "env_key": "NAUKRI_COOKIE"},
    ]

    results = []
    for p in portals:
        cookie_val = os.getenv(p["env_key"], "")
        cookie_len = len(cookie_val)

        if not cookie_val:
            status = "missing"
        elif cookie_len < 50:
            status = "empty"
        else:
            status = "configured"

        results.append(CookieHealth(
            portal=p["name"],
            cookie_configured=status == "configured",
            cookie_length=cookie_len,
            status=status,
        ))

    return results