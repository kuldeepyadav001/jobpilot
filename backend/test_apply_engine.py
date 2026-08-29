import os
import asyncio
from core.database import SessionLocal
from engine.application_service import execute_job_application
from models.job import Job
from models.resume import Resume
from core.config import settings


async def main():
    db = SessionLocal()
    try:
        print("--- Testing Application Engine (Safe Mode) ---")

        test_resume = db.query(Resume).filter(Resume.name == "Python_Backend_Resume").first()
        test_job = db.query(Job).filter(Job.portal == "internshala").first()

        if not test_resume or not test_job:
            print("Missing entities: Ensure you run Stage 3 and 4 verification first.")
            return

        os.makedirs(os.path.dirname(test_resume.file_path), exist_ok=True)
        with open(test_resume.file_path, "w") as f:
            f.write("MOCK PDF DATA STREAM")

        cover_letter = "Hi, I am interested in your open role. Attached is my backend resume."

        # Verify Route 1: Email Dispatch
        print("\nTesting Route 1: Email Dispatch...")
        email_app = await execute_job_application(
            db=db,
            job_id=test_job.id,
            resume_id=test_resume.id,
            cover_letter=cover_letter,
            method="email",
            recipient_email="test-employer@example.com"
        )
        if email_app:
            print(f"SMTP App Status: {email_app.status} | Job Applied Flag: {test_job.is_applied}")

        # Verify Route 2: Portal Automation Action
        print("\nTesting Route 2: Playwright Portal Automation Action...")
        test_job.is_applied = False
        db.commit()

        portal_app = await execute_job_application(
            db=db,
            job_id=test_job.id,
            resume_id=test_resume.id,
            cover_letter=cover_letter,
            method="portal"
        )
        if portal_app:
            print(f"Portal App Status: {portal_app.status}")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())