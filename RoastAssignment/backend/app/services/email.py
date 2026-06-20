"""Email notification service.

Sends a "your assignment has been evaluated" email via SendGrid once an
evaluation completes. This is a best-effort, feature-logs-and-skips
notification: if `SENDGRID_API_KEY` is not configured, or if the SendGrid
call fails for any reason (network error, invalid key, etc.), we log a
warning and return normally. This function must never raise, since callers
(the evaluation pipeline) must not have their own success path broken by an
email delivery failure.
"""
import asyncio
import logging

from app.config import settings

logger = logging.getLogger(__name__)

EXCERPT_LENGTH = 500


def _send_via_sendgrid(to_email: str, subject: str, html_content: str) -> None:
    """Send an email via the SendGrid API. Synchronous (SendGrid SDK is blocking)."""
    import sendgrid
    from sendgrid.helpers.mail import Mail

    sg_client = sendgrid.SendGridAPIClient(settings.SENDGRID_API_KEY)
    message = Mail(
        from_email=settings.EMAIL_FROM_ADDRESS,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )
    sg_client.send(message)


async def send_evaluation_complete_email(submission) -> None:
    """Notify a student by email that their submission has been evaluated.

    `submission` is a `Submission` ORM object with its `.evaluation` relationship
    already loaded by the caller. No-ops (with a warning log) if email is not
    configured. Never raises; any failure is logged as a warning so it cannot
    break the evaluation pipeline that calls this function.
    """
    if not settings.SENDGRID_API_KEY:
        logger.warning("Email skipped: SENDGRID_API_KEY not configured")
        return

    try:
        evaluation = submission.evaluation

        overall_score = evaluation.overall_score if evaluation else None
        roast_text = (evaluation.ai_roast_text if evaluation else None) or ""
        excerpt = roast_text[:EXCERPT_LENGTH]
        if len(roast_text) > EXCERPT_LENGTH:
            excerpt += "..."

        results_url = f"{settings.FRONTEND_URL}/submissions/{submission.id}"
        subject = f"Your assignment '{submission.assignment_name}' has been evaluated"

        html_content = f"""
        <html>
          <body>
            <p>Hi {submission.student_name},</p>
            <p>
              Your submission for <strong>{submission.assignment_name}</strong>
              has been evaluated.
            </p>
            <p><strong>Overall score:</strong> {overall_score}</p>
            <p><strong>Excerpt of feedback:</strong></p>
            <blockquote>{excerpt}</blockquote>
            <p>
              <a href="{results_url}">View your full results</a>
            </p>
          </body>
        </html>
        """

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, _send_via_sendgrid, submission.student_email, subject, html_content
        )
    except Exception as exc:  # noqa: BLE001 - must never raise to the caller
        logger.warning(
            "Failed to send evaluation-complete email for submission_id=%s: %s",
            getattr(submission, "id", None),
            exc,
        )
        return
