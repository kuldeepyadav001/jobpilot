"""Tests for the internship-vs-job classifier."""
from scrapers.service import detect_job_type


def test_detects_internship_terms():
    assert detect_job_type("Software Engineering Intern") == "internship"
    assert detect_job_type("AI/ML Internship") == "internship"
    assert detect_job_type("Graduate Trainee Engineer") == "internship"
    assert detect_job_type("Data Science Apprentice") == "internship"


def test_detects_regular_jobs():
    assert detect_job_type("Senior Python Developer") == "job"
    assert detect_job_type("Backend Engineer - Java") == "job"
    assert detect_job_type("Cloud Solutions Architect") == "job"


def test_no_false_positive_on_internals():
    # 'intern' inside 'internal/internals' must NOT be flagged as an internship.
    assert detect_job_type("Internal Audit Manager") == "job"
    assert detect_job_type("International Sales Executive") == "job"


def test_missing_title_defaults_to_job():
    assert detect_job_type("") == "job"
    assert detect_job_type(None) == "job"
