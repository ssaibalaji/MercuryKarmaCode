"""Tests for app/services/razorpay_service.py.

`create_order` is tested by patching `_get_client` so the real Razorpay SDK
(and network) is never touched - only the paise conversion, receipt shape and
pass-through of the client's response are under test. `verify_webhook_signature`
edge cases (missing secret / missing signature) are covered directly here; the
happy/tamper paths are already covered end-to-end in test_fees.py.
"""
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.config import settings
from app.services import razorpay_service


def test_create_order_converts_amount_to_paise_and_sets_inr_currency(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.order.create.return_value = {"id": "order_abc123", "amount": 19999, "currency": "INR"}
    monkeypatch.setattr(razorpay_service, "_get_client", lambda: fake_client)

    order = razorpay_service.create_order(Decimal("199.99"), student_id=42)

    assert order == {"id": "order_abc123", "amount": 19999, "currency": "INR"}
    call_kwargs: dict[str, Any] = fake_client.order.create.call_args[0][0]
    assert call_kwargs["amount"] == 19999
    assert call_kwargs["currency"] == "INR"
    assert call_kwargs["payment_capture"] == 1
    assert call_kwargs["receipt"].startswith("student-42-")


def test_create_order_rounds_whole_rupee_amount(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.order.create.return_value = {"id": "order_whole", "amount": 50000, "currency": "INR"}
    monkeypatch.setattr(razorpay_service, "_get_client", lambda: fake_client)

    razorpay_service.create_order(Decimal("500"), student_id=7)

    call_kwargs = fake_client.order.create.call_args[0][0]
    assert call_kwargs["amount"] == 50000


def test_verify_webhook_signature_false_when_secret_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "")

    assert razorpay_service.verify_webhook_signature(b'{"event": "payment.captured"}', "some-signature") is False


def test_verify_webhook_signature_false_when_signature_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "a-real-secret")

    assert razorpay_service.verify_webhook_signature(b'{"event": "payment.captured"}', "") is False
