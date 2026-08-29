import asyncio
from core.database import SessionLocal
from scrapers.service import run_all_scrapers
from models.job import Job
from models.company import Company


async def main():
    db = SessionLocal()
    try:
        print("--- Running Test Scraper ---")
        stats = await run_all_scrapers(db, keyword="python", location="remote", max_per_portal=5)
        print("Stats:", stats)

        jobs = db.query(Job).all()
        print(f"\nTotal Jobs in DB: {len(jobs)}")
        for j in jobs[:5]:
            comp = db.query(Company).filter(Company.id == j.company_id).first()
            print(f"[{j.portal.upper()}] {j.title} @ {comp.name} | Location: {j.location} | URL: {j.url[:40]}...")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())