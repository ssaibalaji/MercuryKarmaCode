"""Sync submissions from a Google Forms response sheet into the database.

Reads rows from a Google Sheet (the standard "Form responses" sheet linked to a
Google Form) via the Sheets API and creates `Submission` rows for new entries.
Designed to be called both from the `/submissions/sync` endpoint (manual trigger)
and from the APScheduler job in `app.scheduler` (periodic trigger).
"""
import hashlib
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.submission import Submission, SyncStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

SHEET_RANGE = "A:F"


def get_sheets_service():
    """Build a Google Sheets API client from the configured service account.

    Returns `None` (and logs a warning) if Google Forms sync is not configured,
    so callers can treat sync as a no-op feature rather than crash.
    """
    if not settings.GOOGLE_SERVICE_ACCOUNT_JSON or not settings.GOOGLE_FORMS_SHEET_ID:
        logger.warning(
            "Google Forms sync is not configured (GOOGLE_SERVICE_ACCOUNT_JSON or "
            "GOOGLE_FORMS_SHEET_ID is empty); skipping."
        )
        return None

    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_JSON,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    return build("sheets", "v4", credentials=creds)


def fetch_form_responses(service) -> list[dict]:
    """Read response rows from the configured sheet and normalize them.

    Assumes the standard Google Forms "Form responses" sheet layout:
        Column A: Timestamp
        Column B: Student Name
        Column C: Student Email
        Column D: Assignment Name
        Column E: GitHub Repo URL
        Column F: (unused / reserved)

    Google Forms response sheets have no explicit response-ID column, so we
    derive a stable `google_form_response_id` by hashing
    `timestamp + student_email + assignment_name` (sha256, hex digest). This is
    stable across re-fetches of the same row (idempotency key for `sync_submissions`)
    while still being unique per actual form submission.
    """
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=settings.GOOGLE_FORMS_SHEET_ID, range=SHEET_RANGE)
        .execute()
    )
    rows = result.get("values", [])
    if not rows:
        return []

    # First row is the header row emitted by Google Forms; skip it.
    data_rows = rows[1:]

    responses: list[dict] = []
    for row in data_rows:
        # Pad short rows (Sheets omits trailing empty cells) so indexing is safe.
        padded = row + [""] * (6 - len(row))
        timestamp, student_name, student_email, assignment_name, github_repo_url, _ = padded[:6]

        if not student_email or not assignment_name:
            # Skip blank/malformed rows rather than fabricating a submission.
            continue

        response_id = hashlib.sha256(
            f"{timestamp}|{student_email}|{assignment_name}".encode("utf-8")
        ).hexdigest()

        responses.append(
            {
                "timestamp": timestamp,
                "student_name": student_name,
                "student_email": student_email,
                "assignment_name": assignment_name,
                "github_repo_url": github_repo_url,
                "google_form_response_id": response_id,
            }
        )

    return responses


def _parse_timestamp(raw: str) -> datetime:
    """Best-effort parse of the Google Forms timestamp column; falls back to now()."""
    if raw:
        for fmt in ("%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return datetime.utcnow()


def sync_submissions(db: Session) -> dict:
    """Fetch new Google Form responses and create `Submission` rows for them.

    Idempotent: a response row whose derived `google_form_response_id` already
    exists in the `submissions` table is skipped. Rows whose student email does
    not match an existing `User` with role=student are NOT inserted (the
    `user_id` foreign key is NOT NULL), they are only counted as `unmatched_email`
    so an examiner can see and fix them later (e.g. by inviting/creating the user).

    Returns:
        {
            "created": int,
            "skipped_duplicate": int,
            "unmatched_email": int,
            "created_submissions": list[Submission],
        }
    """
    created_submissions: list[Submission] = []
    created = 0
    skipped_duplicate = 0
    unmatched_email = 0

    service = get_sheets_service()
    if service is None:
        return {
            "created": created,
            "skipped_duplicate": skipped_duplicate,
            "unmatched_email": unmatched_email,
            "created_submissions": created_submissions,
        }

    responses = fetch_form_responses(service)

    for response in responses:
        response_id = response["google_form_response_id"]

        existing = (
            db.query(Submission)
            .filter(Submission.google_form_response_id == response_id)
            .first()
        )
        if existing is not None:
            skipped_duplicate += 1
            continue

        student_email = response["student_email"]
        user: Optional[User] = (
            db.query(User)
            .filter(User.email == student_email, User.role == UserRole.student)
            .first()
        )

        if user is None:
            logger.warning(
                "Google Forms sync: no student user found for email %r "
                "(assignment=%r); skipping submission creation. response_id=%s",
                student_email,
                response["assignment_name"],
                response_id,
            )
            unmatched_email += 1
            continue

        submission = Submission(
            user_id=user.id,
            student_name=response["student_name"],
            student_email=student_email,
            assignment_name=response["assignment_name"],
            github_repo_url=response["github_repo_url"],
            google_form_response_id=response_id,
            sync_status=SyncStatus.synced,
            submitted_at=_parse_timestamp(response["timestamp"]),
        )
        db.add(submission)
        try:
            db.flush()  # assign submission.id; raises IntegrityError on duplicate
        except IntegrityError:
            # Concurrent sync job beat us to this response_id — treat as duplicate.
            db.rollback()
            skipped_duplicate += 1
            logger.warning(
                "Race: duplicate submission for response_id=%s skipped", response_id
            )
            continue
        created_submissions.append(submission)
        created += 1

    db.commit()

    return {
        "created": created,
        "skipped_duplicate": skipped_duplicate,
        "unmatched_email": unmatched_email,
        "created_submissions": created_submissions,
    }
