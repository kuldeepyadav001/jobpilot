from sqlalchemy import Column, Integer, String, Text, Boolean
from core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=True, index=True)
    blacklisted = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)