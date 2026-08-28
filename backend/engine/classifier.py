import re
from typing import Tuple


INTERVIEW_KEYWORDS = [
    r"\binterview\b",
    r"\bschedule a (call|meeting|chat|discussion)\b",
    r"\bshortlisted\b",
    r"\bzoom\.us\b",
    r"\bmeet\.google\.com\b",
    r"\bteams\.microsoft\.com\b",
    r"\bphone screen(ing)?\b",
    r"\bhiring manager\b",
    r"\btechnical round\b",
    r"\bassessment\b"
]

REJECTION_KEYWORDS = [
    r"\bunfortunately\b",
    r"\bnot moving forward\b",
    r"\bother candidates\b",
    r"\bregret to inform\b",
    r"\bdecided not to proceed\b",
    r"\bnot a match\b",
    r"\bposition has been filled\b",
    r"\bwish you (the best|success)\b"
]

CONFIRMATION_KEYWORDS = [
    r"\bapplication received\b",
    r"\bthank you for applying\b",
    r"\bwe have received your\b",
    r"\bsuccessfully submitted\b"
]


def classify_email_content(subject: str, body: str) -> Tuple[str, str]:
    """
    Classifies email text and maps it to an application status.
    Returns: (response_type, mapped_status)
    - response_type: 'interview' | 'rejection' | 'seen' | 'follow_up'
    - mapped_status: 'interview' | 'rejected' | 'viewed' | 'responded'
    """
    combined = f"{subject} {body}".lower()

    # 1. Check for interview signals (highest priority)
    for pattern in INTERVIEW_KEYWORDS:
        if re.search(pattern, combined):
            return "interview", "interview"

    # 2. Check for rejection signals
    for pattern in REJECTION_KEYWORDS:
        if re.search(pattern, combined):
            return "rejection", "rejected"

    # 3. Check for receipt / confirmation signals
    for pattern in CONFIRMATION_KEYWORDS:
        if re.search(pattern, combined):
            return "seen", "viewed"

    # 4. Default: Unclassified recruiter reply
    return "follow_up", "responded"