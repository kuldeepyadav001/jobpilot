"""Tests for the resume↔job matching engine (pure functions, no DB)."""
from models.resume import Resume
from engine.matcher import clean_text, calculate_keyword_coverage, compute_hybrid_match_score


def _resume(text, tags):
    return Resume(
        name="test",
        file_path="/tmp/x.pdf",
        file_type="pdf",
        tags=tags,
        parsed_text=text,
        is_active=True,
    )


def test_clean_text_lowercases_and_strips():
    assert clean_text("Python &Django Dev") == "python django dev"


def test_keyword_coverage_percentage():
    jd = "We need a python developer with fastapi and sqlalchemy experience."
    assert calculate_keyword_coverage(["python", "fastapi", "sqlalchemy"], jd) == 100.0
    assert calculate_keyword_coverage(["python", "golang"], jd) == 50.0


def test_hybrid_score_higher_for_relevant_skills():
    relevant = _resume(
        "Python backend developer with FastAPI, PostgreSQL, Docker, SQLAlchemy, REST APIs.",
        ["python", "fastapi", "docker", "sqlalchemy", "rest api", "postgresql"],
    )
    irrelevant = _resume("Florist who arranges flowers for weddings.", ["flowers", "weddings", "floral"])

    jd = "Backend Python engineer. Required: Python, FastAPI, PostgreSQL, Docker, SQLAlchemy, REST API design."
    rel_score = compute_hybrid_match_score(relevant, jd)
    irr_score = compute_hybrid_match_score(irrelevant, jd)
    assert rel_score > irr_score


def test_hybrid_score_in_expected_range():
    resume = _resume(
        "Python developer. FastAPI, PostgreSQL, Docker.",
        ["python", "fastapi", "postgresql"],
    )
    jd = "We want a Python developer with FastAPI and PostgreSQL."
    score = compute_hybrid_match_score(resume, jd)
    assert 0 <= score <= 100


def test_empty_jd_returns_zero():
    resume = _resume("python", ["python"])
    assert compute_hybrid_match_score(resume, "") == 0.0


def test_coverage_cap_stops_generalist_dilution():
    # A generalist resume listing many skills shouldn't get a tiny score just
    # because one JD tests only a subset of them. Coverage is measured against a
    # capped denominator (default 10), so matching 8/10 "core" skills ≈ 80%.
    assert calculate_keyword_coverage(["python","django","docker","aws","git","linux",
                                       "react","node","sql","redis","celery","pandas"], "python django docker") == 30.0
    # Equivalent matched-count over the cap: 3/10 = 30.0
    assert calculate_keyword_coverage(["python","django","docker","aws","git","linux",
                                       "react","node","sql","redis","celery","pandas"], "python django docker") == 30.0


def test_specialty_resume_not_penalised_by_cap():
    # Few tags => denominator_cap never engages; a great specialty match hits ~100%.
    assert calculate_keyword_coverage(["python", "fastapi"], "python fastapi") == 100.0


def test_good_match_scores_in_high_band():
    # After calibration, a strongly matching JD should land in the 70-95 band so it
    # clears a 40-50 threshold and gets applied to.
    resume = _resume(
        "Python backend developer. FastAPI, PostgreSQL, Docker, SQLAlchemy, REST APIs, AWS, Redis, Celery, Git, Linux.",
        ["python", "fastapi", "docker", "sqlalchemy", "rest api", "postgresql", "aws", "redis", "celery", "git"],
    )
    jd = "Senior Python Backend Engineer. Required: Python, FastAPI, SQLAlchemy, PostgreSQL, Docker, AWS, REST API design, Redis, Celery, Git."
    score = compute_hybrid_match_score(resume, jd)
    assert 70 <= score <= 100


def test_weak_match_stays_low_band():
    resume = _resume("Python developer. FastAPI.", ["python", "fastapi"])
    score = compute_hybrid_match_score(resume, "Java Spring Boot microservices engineer.")
    assert score < 35
