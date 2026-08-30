from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    # Unique Message-ID of the source email — prevents duplicate ingestion on re-scan.
    message_id = Column(String(500), nullable=True, unique=True, index=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    response_type = Column(String(30), nullable=False)
    # interview / rejection / follow_up / seen
    raw_content = Column(Text, nullable=False)
    parsed_summary = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)