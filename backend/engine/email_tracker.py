import imaplib
import email
import re
import unicodedata
from email.header import decode_header
from email.utils import parseaddr
from typing import Any, Optional, Tuple
from sqlalchemy.orm import Session
from loguru import logger
from core.config import settings
from models.application import Application
from models.response import Response
from models.company import Company
from models.job import Job
from engine.classifier import classify_email_content
from engine.application_service import log_status_change


def decode_str(header_val: Any) -> str:
    """Decodes MIME encoded email headers."""
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    result = []
    for text, encoding in decoded_parts:
        if isinstance(text, bytes):
            result.append(text.decode(encoding or "utf-8", errors="ignore"))
        else:
            result.append(str(text))
    return "".join(result)


def extract_body(msg: email.message.Message) -> str:
    """Extracts plain text body from an email object."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="ignore")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="ignore")
    return ""


def _normalize(value: str) -> str:
    """Lowercase, strip non-alphanumeric, and normalize unicode for fuzzy comparison."""
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", value.lower())


def parse_sender(sender_raw: str) -> Tuple[str, str]:
    """
    Splits a raw 'From' header into (display_name, email_address).
    Handles both 'Name <email>' and bare '<email>' / 'email' forms.
    """
    display_name, email_addr = parseaddr(sender_raw)
    display_name = (display_name or "").strip()
    email_addr = (email_addr or "").strip().lower()
    if not email_addr and "<" in sender_raw:
        email_addr = sender_raw.split("<")[-1].rstrip(">").strip().lower()
    return display_name, email_addr


def sender_domain(email_addr: str) -> str:
    """Returns the domain part of an email address (e.g. 'acme.com'), or ''."""
    if not email_addr or "@" not in email_addr:
        return ""
    return email_addr.rsplit("@", 1)[-1].strip().lower()


def compute_sender_match(display_name: str, email_addr: str, company_name: str, job_title: str) -> float:
    """
    Returns a confidence score in [0, 1] that a sender belongs to a given company/job.
    Strict, purpose-built. Higher is better; caller applies a threshold.
    """
    company_norm = _normalize(company_name)
    display_norm = _normalize(display_name)
    addr_domain = sender_domain(email_addr)

    # 1. Exact address-domain match against the company's normalized name
    domain_base = addr_domain.split(".")[0] if addr_domain else ""
    if company_norm and domain_base and company_norm == _normalize(domain_base):
        return 1.0

    # 2. Company name appears prominently in the sender display name (or vice versa)
    if company_norm and display_norm:
        if company_norm in display_norm or display_norm in company_norm:
            return 0.85
        # Common variants: compare significant tokens
        company_tokens = _normalize(company_name).split() if isinstance(company_name, str) else []
        if company_tokens and all(tok in display_norm for tok in company_tokens):
            return 0.8

    # 3. Domain base contains company base (e.g. 'acmetech' vs company 'Acme Tech')
    if company_norm and domain_base and (_normalize(domain_base) in company_norm or company_norm in _normalize(domain_base)):
        return 0.7

    # 4. Job title / company appears in the subject handled by caller (title-based tie-break)
    return 0.0


def match_application_for_email(db: Session, display_name: str, email_addr: str, subject: str) -> Optional[Application]:
    """
    Strictly matches a recruiter email to an application.
    Scans recent applications, scores each candidate, and returns the best with score >= threshold.
    NO 'latest application' fallback — unmatched emails are surfaced for review instead.
    """
    addr_domain = sender_domain(email_addr)
    if not addr_domain:
        return None

    # Candidate applications joined to their company + job
    candidates = (
        db.query(Application, Company, Job)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .order_by(Application.applied_at.desc())
        .limit(60)
        .all()
    )

    best_app = None
    best_score = -1.0
    for app, company, job in candidates:
        score = compute_sender_match(display_name, email_addr, company.name, job.title or "")
        # Subject tie-break: if subject mentions the job title, boost confidence
        if score > 0 and job.title and subject:
            job_title_norm = _normalize(job.title)
            subject_norm = _normalize(subject)
            if job_title_norm and (job_title_norm in subject_norm or subject_norm in job_title_norm):
                score = min(score + 0.15, 1.0)
        if score > best_score:
            best_score = score
            best_app = app

    MATCH_THRESHOLD = 0.6
    if best_app and best_score >= MATCH_THRESHOLD:
        return best_app

    logger.warning(
        f"[Tracker] No confident application match for email "
        f"'{display_name} <{email_addr}>' (domain={addr_domain}, best={best_score:.2f}). "
        "Email left for manual review; NOT auto-attached."
    )
    return None


def process_incoming_email(db: Session, sender: str, subject: str, body: str, message_id: Optional[str] = None) -> Optional[Response]:
    """
    Matches an email to an active Application using strict sender/company matching,
    classifies it, and updates status accordingly. No unsafe 'latest app' fallback.
    """
    response_type, new_status = classify_email_content(subject, body)

    # Dedupe guard: skip if this Message-ID was already ingested.
    if message_id:
        existing = db.query(Response).filter(Response.message_id == message_id).first()
        if existing:
            logger.debug(f"[Tracker] Duplicate email (Message-ID {message_id}) already ingested. Skipping.")
            return None

    display_name, email_addr = parse_sender(sender)
    matching_app = match_application_for_email(db, display_name, email_addr, subject)

    if not matching_app:
        return None

    # Create response record
    response_entry = Response(
        application_id=matching_app.id,
        message_id=message_id,
        response_type=response_type,
        raw_content=f"From: {sender}\nSubject: {subject}\n\n{body[:2000]}",
        parsed_summary=f"Detected {response_type.upper()} via email parser.",
        is_read=False
    )
    db.add(response_entry)

    # Update application status
    old_status = matching_app.status
    if old_status != new_status:
        matching_app.status = new_status
        log_status_change(db, matching_app.id, old_status, new_status, trigger_type="auto")
        logger.info(f"[Tracker] Updated Application #{matching_app.id} status: {old_status} -> {new_status}")

    db.commit()
    return response_entry


def scan_inbox(db: Session, max_emails: int = 10) -> int:
    """
    Connects to IMAP server, reads unread recruiter emails,
    and updates application records.
    """
    if not settings.email_address or not settings.email_app_password:
        logger.warning("[Tracker] Email credentials not configured. Skipping IMAP scan.")
        return 0

    processed_count = 0
    ingested_count = 0
    unmatched_count = 0
    try:
        mail = imaplib.IMAP4_SSL(settings.imap_server, settings.imap_port)
        mail.login(settings.email_address, settings.email_app_password)
        mail.select("inbox")

        # Search for unseen emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK" or not messages[0]:
            mail.close()
            mail.logout()
            return 0

        email_ids = messages[0].split()
        for e_id in email_ids[-max_emails:]:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    sender = decode_str(msg.get("From"))
                    subject = decode_str(msg.get("Subject"))
                    body = extract_body(msg)
                    msg_id = decode_str(msg.get("Message-ID")) or None

                    entered = process_incoming_email(db, sender, subject, body, message_id=msg_id)
                    processed_count += 1
                    if entered is None:
                        unmatched_count += 1
                    else:
                        ingested_count += 1

                    # Mark the message as read on the server so it is never re-ingested.
                    # This is the fix that prevents duplicate responses every scheduler run.
                    try:
                        mail.store(e_id, "+FLAGS", "\\Seen")
                    except Exception as se:
                        logger.debug(f"[Tracker] Could not mark email {e_id} seen: {se}")

        mail.close()
        mail.logout()
        logger.info(
            f"[Tracker] Scanned {processed_count} emails | ingested {ingested_count} | unmatched {unmatched_count}."
        )
        return ingested_count

    except Exception as e:
        logger.error(f"[Tracker] IMAP scanning failed: {e}")
        return 0