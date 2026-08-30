from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    portal = Column(String(50), nullable=False, index=True)  # internshala / naukri
    title = Column(String(500), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    job_type = Column(String(20), default="job", index=True)  # "job" | "internship"
    url = Column(String(1000), unique=True, nullable=False)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    match_score = Column(Float, nullable=True, index=True)
    is_applied = Column(Boolean, default=False, index=True)
    is_blacklisted = Column(Boolean, default=False)