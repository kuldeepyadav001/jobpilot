import re
from typing import List, Optional
from sqlalchemy.orm import Session
from loguru import logger
from models.company import Company
from models.job import Job
from scrapers.base import ScrapedJob
from scrapers.internshala import InternshalaScraper
from scrapers.naukri import NaukriScraper

_JOB_TYPE_WORDS = re.compile(r"\b(internship|intern|trainee|apprentice|co-op|coop)\b", re.IGNORECASE)


def detect_job_type(title: str) -> str:
    """Classifies a posting as an internship or a job from its title."""
    if not title:
        return "job"
    if _JOB_TYPE_WORDS.search(title):
        return "internship"
    return "job"


def save_scraped_jobs(db: Session, scraped_jobs: List[ScrapedJob]) -> dict:
    saved_count = 0
    skipped_existing = 0
    enriched_existing = 0
    blacklisted_count = 0

    for item in scraped_jobs:
        existing_job = db.query(Job).filter(Job.url == item.url).first()

        if existing_job:
            if item.description and len(item.description) > 80 and len(existing_job.description or "") < 80:
                existing_job.description = item.description
                enriched_existing += 1
            else:
                skipped_existing += 1
            continue

        company = db.query(Company).filter(Company.name.ilike(item.company_name.strip())).first()
        if not company:
            company = Company(name=item.company_name.strip(), blacklisted=False)
            db.add(company)
            db.flush()

        if company.blacklisted:
            blacklisted_count += 1
            continue

        new_job = Job(
            portal=item.portal,
            title=item.title,
            company_id=company.id,
            location=item.location,
            salary_min=item.salary_min,
            salary_max=item.salary_max,
            description=item.description,
            url=item.url,
            job_type=detect_job_type(item.title),
            is_applied=False,
            is_blacklisted=False,
        )
        db.add(new_job)
        saved_count += 1

    db.commit()
    return {
        "saved": saved_count,
        "enriched": enriched_existing,
        "skipped": skipped_existing,
        "blacklisted": blacklisted_count,
    }


def _known_urls(db: Session, limit: int = 10000) -> set:
    """Set of job URLs already stored, so re-scrapes skip re-fetching their JDs."""
    try:
        rows = db.query(Job.url).filter(Job.url.isnot(None)).limit(limit).all()
        return {r[0] for r in rows}
    except Exception:
        return set()


async def run_all_scrapers(db: Session, keywords: List[str], location: str = "remote", max_per_portal: int = 10,
                           on_progress=None) -> dict:
    """Runs scrapers over multiple keywords sequentially and returns aggregated stats.

    Each keyword runs in its own try/except so one failing keyword (or a single
    portal failure) never aborts the whole cycle.

    PERFORMANCE: ONE browser per portal is launched and reused across ALL keywords,
    then closed once at the end. (Previously a fresh Chromium was launched and
    closed for every keyword × portal — 20 launches per 10-keyword cycle — which
    spiked CPU and heat on the host.)

    `on_progress(i, keyword)` is called before each keyword so the UI can show
    live "scraping keyword X/Y" progress instead of a bare "running".
    """
    total_stats = {"saved": 0, "enriched": 0, "skipped": 0, "blacklisted": 0}

    logger.info(f"Starting multi-keyword scraper loop. Keywords: {keywords}")

    # Launch the browsers once; reuse them across the whole cycle.
    internshala = InternshalaScraper()
    naukri = NaukriScraper()
    internshala.close_browser_on_scrape = False
    naukri.close_browser_on_scrape = False

    # Jobs we already have descriptions for — skip re-fetching them (huge speedup).
    known = _known_urls(db)

    try:
        idx = 0
        for kw in keywords:
            idx += 1
            kw_clean = kw.strip()
            if not kw_clean:
                continue
            if on_progress:
                try:
                    on_progress(idx, kw_clean)
                except Exception:
                    pass

            logger.info(f"Scraping keyword: '{kw_clean}'")
            try:
                all_jobs = await scrape_keyword(
                    kw_clean, location, max_per_portal,
                    internshala=internshala, naukri=naukri, skip_urls=known,
                )
                stats = save_scraped_jobs(db, all_jobs)
            except Exception as e:
                logger.error(f"[Scraper] Keyword '{kw_clean}' failed (isolated, continuing): {e}")
                stats = {"saved": 0, "enriched": 0, "skipped": 0, "blacklisted": 0}

            for key in total_stats:
                total_stats[key] += stats.get(key, 0)
    finally:
        await internshala.close()
        await naukri.close()

    logger.info(f"Completed multi-keyword scraper run. Aggregated stats: {total_stats}")
    return total_stats


async def scrape_keyword(
    keyword: str,
    location: str,
    max_per_portal: int,
    enrich: bool = True,
    internshala: Optional[InternshalaScraper] = None,
    naukri: Optional[NaukriScraper] = None,
    skip_urls: Optional[set] = None,
) -> List[ScrapedJob]:
    """Scrapes one keyword across all portals and returns the combined raw list (no DB save).

    Pass pre-created `internshala`/`naukri` instances to reuse their browser across
    keywords; otherwise fresh instances (with their own browser) are used.
    """
    internshala = internshala or InternshalaScraper()
    naukri = naukri or NaukriScraper()

    ishala_jobs = await internshala.scrape(keyword=keyword, location=location, max_results=max_per_portal, enrich=enrich, skip_urls=skip_urls)
    naukri_jobs = await naukri.scrape(keyword=keyword, location=location, max_results=max_per_portal, enrich=enrich, skip_urls=skip_urls)
    return ishala_jobs + naukri_jobs


async def scrape_diagnostics(keywords: List[str], location: str, max_per_portal: int) -> dict:
    """Validation harness: runs the scrapers WITHOUT saving to the DB and reports
    per-portal/per-keyword results. Used to verify scrapers work against the live
    portals before trusting the real pipeline."""
    results = []
    # Reuse one browser per portal across all keywords, then close once.
    internshala = InternshalaScraper()
    naukri = NaukriScraper()
    internshala.close_browser_on_scrape = False
    naukri.close_browser_on_scrape = False
    try:
        for kw in keywords:
            kw_clean = kw.strip()
            if not kw_clean:
                continue
            entry = {"keyword": kw_clean, "total": 0, "by_portal": {}, "sample": [], "errors": []}
            for portal_name, scraper in (("internshala", internshala), ("naukri", naukri)):
                try:
                    jobs = await scraper.scrape(keyword=kw_clean, location=location, max_results=max_per_portal, enrich=False)
                    entry["total"] += len(jobs)
                    entry["by_portal"][portal_name] = len(jobs)
                    for j in jobs[:3]:
                        entry["sample"].append({"portal": j.portal, "title": j.title, "company": j.company_name, "url": j.url})
                except Exception as e:
                    entry["errors"].append(f"{portal_name}: {type(e).__name__}: {e}")
            results.append(entry)
    finally:
        await internshala.close()
        await naukri.close()
    return {"results": results, "keywords": keywords, "location": location, "max_per_portal": max_per_portal}