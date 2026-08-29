from typing import List
from sqlalchemy.orm import Session
from loguru import logger
from models.company import Company
from models.job import Job
from scrapers.base import ScrapedJob
from scrapers.internshala import InternshalaScraper
from scrapers.naukri import NaukriScraper


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


async def run_all_scrapers(db: Session, keywords: List[str], location: str = "remote", max_per_portal: int = 10) -> dict:
    """Runs scrapers over multiple keywords sequentially and returns aggregated stats."""
    total_stats = {"saved": 0, "enriched": 0, "skipped": 0, "blacklisted": 0}
    
    logger.info(f"Starting multi-keyword scraper loop. Keywords: {keywords}")
    
    for kw in keywords:
        kw_clean = kw.strip()
        if not kw_clean:
            continue
            
        logger.info(f"Scraping keyword: '{kw_clean}'")
        internshala = InternshalaScraper()
        naukri = NaukriScraper()

        ishala_jobs = await internshala.scrape(keyword=kw_clean, location=location, max_results=max_per_portal)
        naukri_jobs = await naukri.scrape(keyword=kw_clean, location=location, max_results=max_per_portal)

        all_jobs = ishala_jobs + naukri_jobs
        stats = save_scraped_jobs(db, all_jobs)
        
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)

    logger.info(f"Completed multi-keyword scraper run. Aggregated stats: {total_stats}")
    return total_stats