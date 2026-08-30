"""Tests for the rewritten email → application matcher.

Verifies:
- Sender parsing / domain extraction
- Strict domain & display-name scoring
- Correct application is returned, and NO unsafe 'latest application' fallback
- Message-ID dedupe so re-scans never double-ingest
"""
from engine.email_tracker import (
    parse_sender,
    sender_domain,
    compute_sender_match,
    match_application_for_email,
    process_incoming_email,
)
from models.company import Company
from models.job import Job
from models.resume import Resume
from models.application import Application


def _seed(s):
    """Insert one company, one job, one resume, one application; return their ids."""
    comp = Company(name="Acme Tech", blacklisted=False)
    s.add(comp)
    s.flush()

    resume = Resume(name="Backend-Resume", file_path="/tmp/x.pdf", file_type="pdf", tags=["python"])
    s.add(resume)
    s.flush()

    job = Job(
        portal="internshala",
        title="Python Developer",
        company_id=comp.id,
        url="https://internshala.com/jobs/uuid-123",
    )
    s.add(job)
    s.flush()

    app = Application(job_id=job.id, resume_id=resume.id, method="email", status="applied")
    s.add(app)
    s.flush()
    s.commit()
    return comp, job, resume, app


def test_parse_sender_with_name():
    display, addr = parse_sender("Jane Recruiter <jane@acme.com>")
    assert display == "Jane Recruiter"
    assert addr == "jane@acme.com"


def test_parse_sender_bare_email():
    display, addr = parse_sender("<recruiting@acme.com>")
    assert addr == "recruiting@acme.com"


def test_sender_domain():
    assert sender_domain("jane@acme.com") == "acme.com"
    assert sender_domain("no-at-sign") == ""


def test_match_score_exact_domain():
    assert compute_sender_match("Jane", "jane@acme.com", "Acme", "Developer") == 1.0


def test_match_score_display_name_contains_company():
    assert compute_sender_match("Acme Talent Team", "talent@acmerecruit.com", "Acme", "") >= 0.7


def test_match_score_no_match():
    assert compute_sender_match("Bob", "bob@other.com", "Acme", "") < 0.6


def test_matches_correct_application(session):
    comp, job, resume, app = _seed(session)
    matched = match_application_for_email(session, "Acme Recruiter", "hr@acme.com", "Python Developer")
    assert matched is not None
    assert matched.id == app.id


def test_no_fallback_to_latest_application(session):
    comp, job, resume, app = _seed(session)
    # A totally unrelated sender MUST NOT be attached to the application.
    matched = match_application_for_email(session, "Some Bank", "no-reply@unrelatedbank.com", "Your loan")
    assert matched is None


def test_process_incoming_email_dedupes_by_message_id(session):
    comp, job, resume, app = _seed(session)
    sender = "Acme Recruiter <hr@acme.com>"
    subject = "Interview - Python Developer"
    body = "We would like to schedule a Google Meet interview."
    mid = "<deadbeef-123@acme.com>"

    r1 = process_incoming_email(session, sender, subject, body, message_id=mid)
    r2 = process_incoming_email(session, sender, subject, body, message_id=mid)
    assert r1 is not None
    assert r2 is None  # duplicate Message-ID must be skipped
