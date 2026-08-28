from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf / docx
    tags = Column(JSON, nullable=True)  # ["python", "backend", "fresher"]
    version = Column(Integer, default=1)
    parsed_text = Column(Text, nullable=True)  # Extracted text for TF-IDF
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())