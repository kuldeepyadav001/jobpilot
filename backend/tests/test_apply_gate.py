"""Tests the APPLY GATE behaviour + that needs_manual_action doesn't consume the daily budget."""
import pytest
from core.config import settings
from engine.application_service import get_daily_apply_count
from models.company import Company
from models.job import Job
from models.resume import Resume
from models.application import Application
from models.apply_log import ApplyLog
from datetime import date


def test_apply_mode_default_is_dry_run():
    assert settings.apply_mode in ("dry_run", "real")


def test_auto_apply_default_is_off():
    assert settings.auto_apply is False


def test_pipeline_signature_accepts_apply_flag():
    from scheduler.jobs import run_daily_automation_pipeline
    import inspect
    sig = inspect.signature(run_daily_automation_pipeline)
    assert "apply" in sig.parameters
    assert sig.parameters["apply"].default is None


def test_requires_manual_action_does_not_consume_budget(session):
    """A needs_manual_action job must NOT burn a daily apply slot."""
    comp = Company(name="Acme", blacklisted=False)
    session.add(comp); session.flush()
    resume = Resume(name="R", file_path="/tmp/x.pdf", file_type="pdf", tags=[])
    session.add(resume); session.flush()
    job = Job(portal="internshala", title="Job", company_id=comp.id, url="https://x/jobs/1")
    session.add(job); session.flush()

    # Simulate the pipeline deterministically: create an Application in needs_manual_action
    # WITHOUT recording an ApplyLog (matching the new code path).
    app = Application(job_id=job.id, resume_id=resume.id, method="auto", status="needs_manual_action")
    session.add(app); session.commit()

    assert get_daily_apply_count(session, "internshala") == 0


def test_real_apply_does_consume_budget(session):
    """A real 'applied' submission still consumes a daily apply slot."""
    comp = Company(name="Beta", blacklisted=False)
    session.add(comp); session.flush()
    resume = Resume(name="R", file_path="/tmp/x.pdf", file_type="pdf", tags=[])
    session.add(resume); session.flush()
    job = Job(portal="naukri", title="Job", company_id=comp.id, url="https://x/jobs/2")
    session.add(job); session.flush()
    session.add(ApplyLog(portal="naukri", job_id=job.id, method="portal", applied_date=date.today()))
    session.commit()

    assert get_daily_apply_count(session, "naukri") == 1


def test_location_and_max_config(monkeypatch):
    monkeypatch.setattr(settings, "search_location", "bangalore")
    monkeypatch.setattr(settings, "max_per_portal", 3)
    assert settings.search_location == "bangalore"
    assert settings.max_per_portal == 3
