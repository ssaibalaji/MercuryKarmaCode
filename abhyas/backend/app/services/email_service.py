"""Email-sending abstraction used by the Fees module (and future modules).

No real email provider is wired up yet. `send_email` is the single integration
point: it currently logs the message instead of calling a provider. When a
provider (e.g. SendGrid/SES) is chosen, only this function's body needs to
change - callers (fee_service.send_reminder, etc.) are unaffected.
"""
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email to `to`. Returns True if the send was accepted.

    Stub implementation: logs the email instead of dispatching it via a real
    provider until EMAIL_SERVICE_API_KEY is wired to one.
    """
    if not settings.EMAIL_SERVICE_API_KEY:
        logger.info(
            "EMAIL_SERVICE_API_KEY not configured; logging email instead of sending. "
            "to=%s from=%s subject=%s",
            to,
            settings.EMAIL_FROM_ADDRESS,
            subject,
        )
    else:
        logger.info(
            "Sending email to=%s from=%s subject=%s",
            to,
            settings.EMAIL_FROM_ADDRESS,
            subject,
        )
    logger.debug("Email body for to=%s: %s", to, body)
    return True
