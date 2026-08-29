from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.sql import func
from core.database import Base


class ApplyLog(Base):
    __tablename__ = "apply_log"

    id = Column(Integer, primary_key=True, index=True)
    portal = Column(String(50), nullable=False, index=True)
    job_id = Column(Integer, nullable=False)
    method = Column(String(20), nullable=False)  # email / portal / manual
    applied_date = Column(Date, nullable=False, index=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())