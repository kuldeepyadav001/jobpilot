import re
from typing import List, Optional
from sqlalchemy.orm import Session
from loguru import logger
from models.company import Company
from models.job import Job
from scrapers.base import ScrapedJob
from scrapers.internshala import InternshalaScraper
from scrapers.naukri import NaukriScraper
from scrapers.registry import build_scraper, scraper_ids
from scrapers.freshersworld import FreshersworldScraper

_JOB_TYPE_WORDS = re.compile(r"\b(internship|intern|trainee|apprentice|co-op|coop)\b", re.IGNORECASE)


def detect_job_type(title: str) -> str:
    """Classifies a posting as an internship or a job from its title."""
    if not title:
        return "job"
    if _JOB_TYPE_WORDS.search(title):
        return "internship"
    return "job"


def _resolve_job_type(portal: str, section_type: Optional[str], title: str) -> str:
    """Authoritative job_type decision.

    Internshala is split into two honest sections, so its chosen section is the
    source of truth (an internship-section posting is an internship even if the
    title doesn't say 'intern' — e.g. 'Data Scientist' in /internships/).
    Naukri mixes jobs+internships in one listing, so we rely on the title there.
    We also never overrule an explicit 'internship' from the title.
    """
    if section_type == "internship" or detect_job_type(title) == "internship":
        return "internship"
    return "job"


def _is_internships_only(job_types: Optional[List[str]]) -> bool:
    """True when the user chose ONLY the internships section (skip Naukri)."""
    if not job_types:
        return False
    return [t.strip() for t in job_types if t.strip()] == ["internships"]


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
            job_type=_resolve_job_type(item.portal, item.job_type, item.title),
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
                           on_progress=None, job_types: Optional[List[str]] = None,
                           naukri_keywords: Optional[List[str]] = None) -> dict:
    """Runs scrapers over multiple keywords sequentially and returns aggregated stats.

    Each keyword runs in its own try/except so one failing keyword (or a single
    portal failure) never aborts the whole cycle.

    PERFORMANCE: ONE browser per portal is launched and reused across ALL keywords,
    then closed once at the end.

    JOB vs INTERNSHIP: `job_types` selects which Internshala sections to scrape.
      - ['jobs']        -> only  /jobs/{kw}-jobs        (annual salary)
      - ['internships'] -> only /internships/{kw}-internships (stipend)
      - ['jobs','internships'] (default) -> both, tagged separately.
    Naukri only has jobs, so it is always scraped as jobs.

    PER-PORTAL KEYWORDS: Internshala uses `keywords`; Naukri uses `naukri_keywords`
    (falling back to `keywords`). Naukri matches short/precise role terms far
    better than long generic ones.

    `on_progress(i, label)` is called before each keyword so the UI can show live
    "scraping keyword X/Y" progress instead of a bare "running".
    """
    job_types = job_types or ["jobs", "internships"]
    naukri_kws = [k.strip() for k in (naukri_keywords or keywords) if k.strip()]
    internshala_kws = [k.strip() for k in keywords if k.strip()]
    total_stats = {"saved": 0, "enriched": 0, "skipped": 0, "blacklisted": 0}

    # Naukri only lists JOBS. If the user chose internships-only, skip Naukri so we
    # don't pull full-time jobs into an internship-only feed.
    skip_naukri = _is_internships_only(job_types)

    logger.info(f"Starting multi-keyword scraper loop. Internshala: {internshala_kws}, "
                f"Naukri: {naukri_kws}, types: {job_types}, skip_naukri: {skip_naukri}")

    # Launch the browsers once; reuse them across the whole cycle.
    internshala = InternshalaScraper()
    naukri = NaukriScraper()
    freshersworld = FreshersworldScraper()
    internshala.close_browser_on_scrape = False
    naukri.close_browser_on_scrape = False
    freshersworld.close_browser_on_scrape = False

    # Jobs we already have descriptions for — skip re-fetching them (huge speedup).
    known = _known_urls(db)

    counter = 0

    try:
        # --- Internshala (uses the broad keywords for each selected section) ---
        for jt in job_types:
            for kw in internshala_kws:
                counter += 1
                if on_progress:
                    try:
                        on_progress(counter, f"Internshala {jt.rstrip('s')}: {kw}")
                    except Exception:
                        pass
                logger.info(f"Scraping Internshala '{kw}' ({jt})")
                try:
                    stats = save_scraped_jobs(db, await internshala.scrape(
                        keyword=kw, location=location, max_results=max_per_portal,
                        enrich=True, skip_urls=known,
                        job_type="internship" if jt == "internships" else "job",
                    ))
                except Exception as e:
                    logger.error(f"[Scraper] Internshala '{kw}' ({jt}) failed (isolated): {e}")
                    stats = {"saved": 0, "enriched": 0, "skipped": 0, "blacklisted": 0}
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)

        # --- Naukri (uses tighter keywords; always jobs) ---
        # Skipped when the user chose internships-only (Naukri has no internships).
        if not skip_naukri:
            for kw in naukri_kws:
                counter += 1
                if on_progress:
                    try:
                        on_progress(counter, f"Naukri: {kw}")
                    except Exception:
                        pass
                logger.info(f"Scraping Naukri '{kw}'")
                try:
                    stats = save_scraped_jobs(db, await naukri.scrape(
                        keyword=kw, location=location, max_results=max_per_portal,
                        enrich=True, skip_urls=known, job_type="job",
                    ))
                except Exception as e:
                    logger.error(f"[Scraper] Naukri '{kw}' failed (isolated): {e}")
                    stats = {"saved": 0, "enriched": 0, "skipped": 0, "blacklisted": 0}
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)
        else:
            logger.info("[Scraper] Internships-only mode: skipping Naukri (jobs only).")

        # --- Freshersworld (supports jobs AND internships; uses broad keywords) ---
        for jt in job_types:
            for kw in internshala_kws:
                counter += 1
                if on_progress:
                    try:
                        on_progress(counter, f"Freshersworld {jt.rstrip('s')}: {kw}")
                    except Exception:
                        pass
                logger.info(f"Scraping Freshersworld '{kw}' ({jt})")
                try:
                    stats = save_scraped_jobs(db, await freshersworld.scrape(
                        keyword=kw, location=location, max_results=max_per_portal,
                        enrich=True, skip_urls=known,
                        job_type="internship" if jt == "internships" else "job",
                    ))
                except Exception as e:
                    logger.error(f"[Scraper] Freshersworld '{kw}' ({jt}) failed (isolated): {e}")
                    stats = {"saved": 0, "enriched": 0, "skipped": 0, "blacklisted": 0}
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)
    finally:
        await internshala.close()
        await naukri.close()
        await freshersworld.close()

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
    job_type: str = "job",
) -> List[ScrapedJob]:
    """Scrapes one keyword across all portals and returns the combined raw list (no DB save).

    `job_type` = 'job' or 'internship'. Internshala routes to the matching section;
    Naukri only lists jobs (its `job_type` is forced to 'job' regardless).
    """
    internshala = internshala or InternshalaScraper()
    naukri = naukri or NaukriScraper()

    ishala_jobs = await internshala.scrape(
        keyword=keyword, location=location, max_results=max_per_portal,
        enrich=enrich, skip_urls=skip_urls, job_type=job_type,
    )
    naukri_jobs = await naukri.scrape(
        keyword=keyword, location=location, max_results=max_per_portal,
        enrich=enrich, skip_urls=skip_urls, job_type="job",
    )
    return ishala_jobs + naukri_jobs


async def scrape_diagnostics(keywords: List[str], location: str, max_per_portal: int) -> dict:
    """Validation harness: runs the scrapers WITHOUT saving to the DB and reports
    per-portal/per-keyword results. Used to verify scrapers work against the live
    portals before trusting the real pipeline."""
    results = []
    # Use the registry so every registered portal is covered automatically.
    scrapers = {pid: build_scraper(pid) for pid in scraper_ids()}
    for s in scrapers.values():
        s.close_browser_on_scrape = False
    try:
        for kw in keywords:
            kw_clean = kw.strip()
            if not kw_clean:
                continue
            entry = {"keyword": kw_clean, "total": 0, "by_portal": {}, "sample": [], "errors": []}
            for portal_name, scraper in scrapers.items():
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
        for s in scrapers.values():
            await s.close()
    return {"results": results, "keywords": keywords, "location": location, "max_per_portal": max_per_portal}