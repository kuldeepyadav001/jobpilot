from typing import List
from sqlalchemy.orm import Session
from loguru import logger
from models.company import Company
from models.job import Job
from scrapers.base import ScrapedJob
from scrapers.internshala import InternshalaScraper
from scrapers.naukri import NaukriScraper


def save_scraped_jobs(db: Session, scraped_jobs: List[ScrapedJob]) -> dict:
    """
    Saves scraped jobs to DB:
    1. Checks company blacklist
    2. Finds or creates Company record
    3. Ignores duplicates (by URL)
    """
    saved_count = 0
    skipped_existing = 0
    blacklisted_count = 0

    for item in scraped_jobs:
        # Check if job already exists
        existing_job = db.query(Job).filter(Job.url == item.url).first()
        if existing_job:
            skipped_existing += 1
            continue

        # Find or create company
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
    logger.info(f"Ingestion complete: {saved_count} saved, {skipped_existing} existing, {blacklisted_count} blacklisted.")
    return {
        "saved": saved_count,
        "skipped": skipped_existing,
        "blacklisted": blacklisted_count,
    }


async def run_all_scrapers(db: Session, keyword: str = "python developer", location: str = "remote", max_per_portal: int = 15) -> dict:
    """Runs Internshala and Naukri scrapers and ingests results."""
    internshala = InternshalaScraper()
    naukri = NaukriScraper()

    logger.info(f"Starting scraper run for keyword='{keyword}', location='{location}'")
    internshala_jobs = await internshala.scrape(keyword=keyword, location=location, max_results=max_per_portal)
    naukri_jobs = await naukri.scrape(keyword=keyword, location=location, max_results=max_per_portal)

    all_jobs = internshala_jobs + naukri_jobs
    return save_scraped_jobs(db, all_jobs)