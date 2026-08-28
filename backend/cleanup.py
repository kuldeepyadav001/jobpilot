from core.database import SessionLocal
from models.response import Response
from models.status_history import StatusHistory
from models.application import Application
from models.analytics import AnalyticsSnapshot
from models.job import Job
from models.company import Company
from models.resume import Resume

db = SessionLocal()

counts = {
    "responses": db.query(Response).delete(),
    "status_history": db.query(StatusHistory).delete(),
    "applications": db.query(Application).delete(),
    "analytics": db.query(AnalyticsSnapshot).delete(),
    "jobs": db.query(Job).delete(),
    "companies": db.query(Company).delete(),
    "resumes": db.query(Resume).delete(),
}

db.commit()

for table, count in counts.items():
    print(f"  Deleted {count} rows from {table}")

print("\nAll test/sample data cleared.")
db.close()