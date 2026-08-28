from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    old_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    trigger = Column(String(10), nullable=False)  # auto / manual