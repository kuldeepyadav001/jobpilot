import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional
from datetime import datetime
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


def process_incoming_email(db: Session, sender: str, subject: str, body: str) -> Optional[Response]:
    """
    Matches an email to an active Application in the DB,
    classifies it, and updates status accordingly.
    """
    response_type, new_status = classify_email_content(subject, body)

    # Find matching company by domain or sender name
    matching_app = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .filter(
            Company.name.ilike(f"%{sender}%") |
            Job.title.ilike(f"%{subject}%")
        )
        .order_by(Application.applied_at.desc())
        .first()
    )

    if not matching_app:
        # Fallback: link to latest active application if exists
        matching_app = db.query(Application).order_by(Application.applied_at.desc()).first()

    if not matching_app:
        logger.debug(f"[Tracker] No matching application found for email from '{sender}'")
        return None

    # Create response record
    response_entry = Response(
        application_id=matching_app.id,
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

                    process_incoming_email(db, sender, subject, body)
                    processed_count += 1

        mail.close()
        mail.logout()
        logger.info(f"[Tracker] Scanned and processed {processed_count} emails.")
        return processed_count

    except Exception as e:
        logger.error(f"[Tracker] IMAP scanning failed: {e}")
        return 0