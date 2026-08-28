from sqlalchemy import Column, Integer, Date, JSON
from core.database import Base


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshot"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True)
    total_applied = Column(Integer, default=0)
    total_responses = Column(Integer, default=0)
    total_interviews = Column(Integer, default=0)
    portal_breakdown = Column(JSON, nullable=True)
    # {"internshala": 12, "naukri": 8}