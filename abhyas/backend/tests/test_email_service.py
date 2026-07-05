"""Direct unit tests for the email_service stub (app/services/email_service.py).

`send_email` always returns True, but logs a different message depending on
whether EMAIL_SERVICE_API_KEY is configured. Both branches are asserted via
caplog rather than just checking the return value, since the log message is
the only observable difference between the two code paths.
"""
import logging

import pytest

from app.config import settings
from app.services.email_service import send_email


def test_send_email_without_api_key_logs_stub_message_and_returns_true(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(settings, "EMAIL_SERVICE_API_KEY", "")

    with caplog.at_level(logging.INFO, logger="app.services.email_service"):
        result = send_email(to="parent@example.com", subject="Reminder", body="Please pay your fees.")

    assert result is True
    assert any("not configured" in record.message for record in caplog.records)
    assert any("parent@example.com" in record.message for record in caplog.records)


def test_send_email_with_api_key_logs_sending_message_and_returns_true(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(settings, "EMAIL_SERVICE_API_KEY", "real-provider-key")

    with caplog.at_level(logging.INFO, logger="app.services.email_service"):
        result = send_email(to="parent@example.com", subject="Reminder", body="Please pay your fees.")

    assert result is True
    messages = [record.message for record in caplog.records]
    assert any(msg.startswith("Sending email") for msg in messages)
    assert not any("not configured" in msg for msg in messages)
