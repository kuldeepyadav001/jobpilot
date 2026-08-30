import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from loguru import logger
from core.config import settings


def send_job_application_email(
    to_email: str,
    subject: str,
    body_text: str,
    resume_path: str,
    resume_name: str
) -> bool:
    """Dispatches a job application email with the resume attached."""
    if not settings.email_address or not settings.email_app_password:
        logger.error("[SMTP] Email credentials not configured in environment.")
        return False

    # APPLY GATE: Only send to the real recipient when apply_mode='real'.
    # Otherwise reroute to self so nothing is actually dispatched to an employer.
    if settings.apply_mode != "real":
        logger.warning(f"[SMTP] DRY_RUN: rerouting email meant for <{to_email}> to self <{settings.email_address}>. Set APPLY_MODE=real to send for real.")
        to_email = settings.email_address

    msg = MIMEMultipart()
    msg["From"] = settings.email_address
    msg["To"] = to_email
    msg["Subject"] = subject

    # Inject cover letter / body text
    msg.attach(MIMEText(body_text, "plain"))

    # Attach resume file
    if not os.path.exists(resume_path):
        logger.error(f"[SMTP] Resume attachment file not found: {resume_path}")
        return False

    try:
        with open(resume_path, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="pdf")
            attachment.add_header("Content-Disposition", "attachment", filename=resume_name)
            msg.attach(attachment)
    except Exception as e:
        logger.error(f"[SMTP] Failed to read resume attachment: {e}")
        return False

    try:
        logger.info(f"[SMTP] Connecting to server {settings.smtp_server}:{settings.smtp_port}...")
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.email_address, settings.email_app_password)
            server.send_message(msg)
            logger.info(f"[SMTP] Email successfully dispatched to {to_email}")
            return True
    except Exception as e:
        logger.error(f"[SMTP] Connection or sending failed: {e}")
        return False