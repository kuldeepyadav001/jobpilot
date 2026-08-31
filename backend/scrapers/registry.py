"""Portal registry — makes adding a new job/internship platform easy.

Each scraper subclasses BaseScraper and exposes a `portal` attribute (its id) and
`supports_jobs` / `supports_internships` booleans. To add a portal:
  1. Write a scraper class in scrapers/scrape_<name>.py (subclass BaseScraper).
  2. Register it in the VALUE_HANDLERS dict below.
  3. Optionally wire per-portal keywords into config.

New portals are discovered automatically by run_all_scrapers and the diagnostics
harness, so no pipeline changes are needed.
"""
from __future__ import annotations

from typing import Dict, List, Type

from scrapers.base import BaseScraper
from scrapers.internshala import InternshalaScraper
from scrapers.naukri import NaukriScraper
from scrapers.freshersworld import FreshersworldScraper


def _registry() -> Dict[str, Type[BaseScraper]]:
    return {
        "internshala": InternshalaScraper,
        "naukri": NaukriScraper,
        "freshersworld": FreshersworldScraper,
    }


def all_scrapers() -> List[Type[BaseScraper]]:
    """All registered scraper classes."""
    return list(_registry().values())


def scraper_ids() -> List[str]:
    return list(_registry().keys())


def build_scraper(portal_id: str) -> BaseScraper:
    cls = _registry().get(portal_id)
    if cls is None:
        raise ValueError(f"Unknown portal: {portal_id}")
    return cls()
