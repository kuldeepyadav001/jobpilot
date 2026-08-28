from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    method = Column(String(20), nullable=False)  # email / portal
    status = Column(String(20), default="applied", index=True)
    # applied → viewed → responded → interview → offer → rejected
    cover_letter = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)