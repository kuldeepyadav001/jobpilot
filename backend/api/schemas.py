from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


# --- Jobs ---
class JobOut(BaseModel):
    id: int
    portal: str
    title: str
    company_name: str
    location: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    description: Optional[str]
    url: str
    match_score: Optional[float]
    is_applied: bool
    scraped_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    jobs: List[JobOut]


# --- Applications ---
class ApplicationOut(BaseModel):
    id: int
    job_id: int
    job_title: Optional[str]
    company_name: Optional[str]
    resume_id: int
    applied_at: Optional[datetime]
    method: str
    status: str
    cover_letter: Optional[str]

    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    status: str  # applied | viewed | responded | interview | offer | rejected


# --- Resumes ---
class ResumeOut(BaseModel):
    id: int
    name: str
    file_type: str
    tags: Optional[List[str]]
    version: int
    is_active: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Analytics ---
class DashboardStats(BaseModel):
    total_jobs: int
    total_applied: int
    total_interviews: int
    total_rejected: int
    avg_match_score: Optional[float]
    portal_breakdown: dict


class SnapshotOut(BaseModel):
    date: date
    total_applied: int
    total_responses: int
    total_interviews: int

    class Config:
        from_attributes = True


# --- Pipeline ---
class PipelineResponse(BaseModel):
    status: str
    message: str
    
class DashboardStats(BaseModel):
    total_jobs: int
    total_applied: int
    total_interviews: int
    total_rejected: int
    avg_match_score: Optional[float]
    portal_breakdown: dict
    daily_applies: int = 0
    daily_cap: int = 10    