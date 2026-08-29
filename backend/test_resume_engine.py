from core.database import SessionLocal
from engine.service import register_resume
from engine.matcher import select_best_resume
from models.resume import Resume
from models.job import Job
from models.company import Company


def main():
    db = SessionLocal()
    try:
        print("--- Testing Hybrid Resume Engine ---")

        # 1. Fetch or register test resume with rich tech tags
        test_resume = db.query(Resume).filter(Resume.name == "Python_Backend_Resume").first()
        tags = [
            "python", "fastapi", "postgresql", "docker", "sqlalchemy",
            "rest api", "git", "playwright", "microservices", "sql"
        ]

        if not test_resume:
            sample_resume_text = """
            Experienced Python Backend Developer with strong skills in FastAPI, PostgreSQL,
            Docker, SQLAlchemy, and REST API design. Familiar with automated web scraping
            using Playwright, asynchronous programming, Git version control, and cloud deployments.
            Hands-on experience building scalable microservices and data pipelines.
            """
            test_resume = register_resume(
                db=db,
                name="Python_Backend_Resume",
                file_path="/app/resumes/sample_resume.pdf",
                file_type="pdf",
                tags=tags,
                raw_text=sample_resume_text
            )
        else:
            # Ensure test resume has tags attached
            test_resume.tags = tags
            db.commit()

        active_resumes = db.query(Resume).filter(Resume.is_active == True).all()
        jobs = db.query(Job).all()

        print(f"Active Resumes: {len(active_resumes)} | Total Jobs to Score: {len(jobs)}")

        # 2. Re-score all jobs using the hybrid engine
        for j in jobs:
            jd_text = f"{j.title} {j.description or ''}"
            best_resume, score = select_best_resume(jd_text, active_resumes)
            j.match_score = score

        db.commit()
        print(f"Scored {len(jobs)} jobs successfully.\n")

        # 3. Print ranked results
        print("--- Ranked Matching Jobs (Hybrid ATS Scores) ---")
        ranked_jobs = db.query(Job).order_by(Job.match_score.desc()).all()
        for j in ranked_jobs:
            comp = db.query(Company).filter(Company.id == j.company_id).first()
            comp_name = comp.name if comp else "Unknown"
            print(f"Match: {j.match_score:5.2f}% | [{j.portal.upper()}] {j.title[:40]} @ {comp_name}")

    finally:
        db.close()


if __name__ == "__main__":
    main()