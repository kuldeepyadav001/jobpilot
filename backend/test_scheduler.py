import asyncio
from scheduler.jobs import run_daily_automation_pipeline
from core.database import SessionLocal
from models.job import Job
from models.application import Application
from models.analytics import AnalyticsSnapshot


async def main():
    print("--- Testing Automation Pipeline Execution ---")
    
    # Execute full pipeline sequentially
    await run_daily_automation_pipeline()
    
    # Verify DB state outcomes
    db = SessionLocal()
    try:
        print("\n--- Pipeline Execution Post-Verification ---")
        jobs_scraped = db.query(Job).count()
        applied_apps = db.query(Application).count()
        snapshots = db.query(AnalyticsSnapshot).all()
        
        print(f"Total Jobs in database: {jobs_scraped}")
        print(f"Total Applications submitted: {applied_apps}")
        print(f"Snapshots logged: {len(snapshots)}")
        for s in snapshots:
            print(f"  - Snapshot Date {s.date}: Applied={s.total_applied}, Interviews={s.total_interviews}")
            
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())