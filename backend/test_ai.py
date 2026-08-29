import asyncio
from core.database import SessionLocal
from models.job import Job
from models.resume import Resume
from models.company import Company
from ai.cover_letter import generate_tailored_cover_letter


async def main():
    db = SessionLocal()
    try:
        print("--- Testing AI Layer & Fallback Engine ---")

        test_job = db.query(Job).first()
        test_resume = db.query(Resume).first()

        if not test_job or not test_resume:
            print("Missing DB data: Ensure stages 2, 3, and 4 are complete.")
            return

        company = db.query(Company).filter(Company.id == test_job.company_id).first()
        company_name = company.name if company else "Company"

        cover_letter = await generate_tailored_cover_letter(
            job_title=test_job.title,
            company_name=company_name,
            job_description=test_job.description or test_job.title,
            resume_text=test_resume.parsed_text or ""
        )

        print("\n--- Generated Output ---")
        print(cover_letter)
        print("------------------------\n")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())