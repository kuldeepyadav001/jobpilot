"""Tests for the weekly stale-job cleanup (deterministic via injected `now`)."""
from datetime import datetime, timedelta, timezone
from core.config import settings
from engine.maintenance import cleanup_stale_jobs
from models.company import Company
from models.job import Job
from models.resume import Resume
from models.application import Application


def _mkjob(session, comp_id, url, scraped_at, is_applied=False, title="Job"):
    j = Job(portal="internshala", title=title, company_id=comp_id, url=url,
            scraped_at=scraped_at, is_applied=is_applied)
    session.add(j); session.flush()
    return j


def _seed(session):
    comp = Company(name="Acme", blacklisted=False)
    session.add(comp); session.flush()
    return comp.id


def test_cleanup_removes_stale_unapplied_only(session):
    now = datetime(2026, 8, 30, tzinfo=timezone.utc)
    old = now - timedelta(days=40)
    recent = now - timedelta(days=2)
    cid = _seed(session)
    _mkjob(session, cid, "https://x/jobs/a", scraped_at=old)              # stale + unapplied -> delete
    _mkjob(session, cid, "https://x/jobs/b", scraped_at=old, is_applied=True)  # applied -> keep
    _mkjob(session, cid, "https://x/jobs/c", scraped_at=recent)           # fresh -> keep
    session.commit()

    res = cleanup_stale_jobs(session, retention_days=30, enabled=True, now=now)
    assert res["deleted"] == 1
    remaining = {j.url for j in session.query(Job).all()}
    assert remaining == {"https://x/jobs/b", "https://x/jobs/c"}


def test_cleanup_keeps_jobs_referenced_by_application(session):
    now = datetime(2026, 8, 30, tzinfo=timezone.utc)
    old = now - timedelta(days=40)
    cid = _seed(session)
    job = _mkjob(session, cid, "https://x/jobs/referenced", scraped_at=old)
    resume = Resume(name="R", file_path="/tmp/x.pdf", file_type="pdf", tags=[])
    session.add(resume); session.flush()
    # A needs_manual_action application references this job -> must be kept.
    session.add(Application(job_id=job.id, resume_id=resume.id, method="auto", status="needs_manual_action"))
    session.commit()

    res = cleanup_stale_jobs(session, retention_days=30, enabled=True, now=now)
    assert res["deleted"] == 0
    assert session.query(Job).filter(Job.url == "https://x/jobs/referenced").count() == 1


def test_cleanup_disabled(session):
    now = datetime(2026, 8, 30, tzinfo=timezone.utc)
    old = now - timedelta(days=40)
    cid = _seed(session)
    _mkjob(session, cid, "https://x/jobs/a", scraped_at=old)
    session.commit()
    res = cleanup_stale_jobs(session, enabled=False, now=now)
    assert res["deleted"] == 0
    assert session.query(Job).count() == 1


def test_cleanup_null_scraped_at_kept(session):
    now = datetime(2026, 8, 30, tzinfo=timezone.utc)
    cid = _seed(session)
    j = Job(portal="internshala", title="Job", company_id=cid, url="https://x/jobs/no-ts", scraped_at=None)
    session.add(j); session.commit()
    res = cleanup_stale_jobs(session, retention_days=1, enabled=True, now=now)
    assert res["deleted"] == 0
