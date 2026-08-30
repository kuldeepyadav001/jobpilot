"""Scraper diagnostic + control endpoints (single-user local tool)."""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List

from core.config import settings
from scrapers.service import scrape_diagnostics

router = APIRouter(prefix="/scrapers", tags=["Scrapers"])


class ScrapeDiagResponse(BaseModel):
    results: List[dict]
    keywords: List[str]
    location: str
    max_per_portal: int


@router.get("/diagnostics", response_model=ScrapeDiagResponse)
async def diagnostics(
    keywords: str = Query(None, description="Comma-separated keywords. Defaults to SEARCH_KEYWORDS."),
    location: str = Query(None),
    max_per_portal: int = Query(None, ge=1, le=50),
):
    """DRY-RUN: scrapes the portals but saves nothing, then reports how many
    jobs each portal/keyword actually returned + a few samples. Use this to
    validate the scrapers against the LIVE portals before trusting the pipeline."""
    kw_list = _resolve_keywords(keywords)
    env_location = location or settings.search_location
    mpp = max_per_portal or settings.max_per_portal

    report = await scrape_diagnostics(kw_list, env_location, mpp)
    return ScrapeDiagResponse(
        results=report["results"],
        keywords=kw_list,
        location=env_location,
        max_per_portal=mpp,
    )


def _resolve_keywords(keywords: str) -> List[str]:
    if keywords and keywords.strip():
        return [k.strip() for k in keywords.split(",") if k.strip()]
    kv = [k.strip() for k in settings.search_keywords.split(",") if k.strip()]
    return kv or ["python developer"]
