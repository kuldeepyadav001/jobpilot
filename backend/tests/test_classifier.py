"""Unit tests for the email → response-type classifier (no DB required)."""
from engine.classifier import classify_email_content


def test_interview_detection():
    resp, status = classify_email_content(
        "Interview Invitation - Backend Role",
        "Hi, we'd like to schedule a Zoom interview next Monday.",
    )
    assert resp == "interview"
    assert status == "interview"


def test_rejection_detection():
    resp, status = classify_email_content(
        "Update regarding your application",
        "Thank you for your interest. Unfortunately, we have decided to move forward with other candidates.",
    )
    assert resp == "rejection"
    assert status == "rejected"


def test_confirmation_detection():
    resp, status = classify_email_content(
        "Application Received",
        "Thank you for applying. We have received your application.",
    )
    assert resp == "seen"
    assert status == "viewed"


def test_generic_reply_defaults_to_follow_up():
    resp, status = classify_email_content(
        "Question about your application",
        "Could you share your availability this week?",
    )
    assert resp == "follow_up"
    assert status == "responded"


def test_interview_takes_priority_over_rejection_words():
    # Some emails contain both words; interview must win.
    resp, _ = classify_email_content(
        "Interview at XYZ",
        "Unfortunately we had many candidates but we would like to schedule a Google Meet interview.",
    )
    assert resp == "interview"
