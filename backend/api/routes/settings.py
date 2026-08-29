import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/settings", tags=["Settings"])


class CookieHealth(BaseModel):
    portal: str
    cookie_configured: bool
    cookie_length: int
    status: str  # "configured" | "missing" | "empty"


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