"""Send email via SMTP using app config."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body_plain: str, body_html: str | None = None) -> None:
    """Send an email. Uses MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD from config."""
    if not settings.MAIL_SERVER or not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.warning("Mail not configured (MAIL_SERVER/MAIL_USERNAME/MAIL_PASSWORD). Skipping send.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_USERNAME
    msg["To"] = to
    msg.attach(MIMEText(body_plain, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.MAIL_SERVER, 587) as server:
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_USERNAME, to, msg.as_string())
        logger.info("Email sent to %s", to)
    except Exception as e:
        logger.exception("Failed to send email to %s: %s", to, e)
        raise
