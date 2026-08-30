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
