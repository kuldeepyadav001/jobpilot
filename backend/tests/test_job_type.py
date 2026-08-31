"""Tests for the internship-vs-job classifier + section URL routing."""
from scrapers.service import detect_job_type
from scrapers.internshala import InternshalaScraper


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


def test_search_url_routes_to_correct_section():
    s = InternshalaScraper()
    assert "internships/python-developer-internships" in s._search_url("python developer", "internship", "")
    assert "jobs/python-developer-jobs" in s._search_url("python developer", "job", "")
    # Location appends correctly.
    assert "jobs/java-developer-jobs-in-remote" in s._search_url("java developer", "job", "remote")
