"""Razorpay integration: order creation and webhook signature verification."""
import hashlib
import hmac
import logging
import time
from decimal import Decimal
from typing import Any

import razorpay

from app.config import settings

logger = logging.getLogger(__name__)


def _get_client() -> razorpay.Client:
    """Build a Razorpay SDK client from configured API credentials."""
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_order(amount: Decimal, student_id: int) -> dict[str, Any]:
    """Create a Razorpay order for `amount` rupees against a given student.

    Returns the raw Razorpay order dict (contains at least `id`, `amount`,
    `currency`). Amount is converted to the smallest currency unit (paise).
    """
    client = _get_client()
    amount_paise = int((amount * 100).to_integral_value())
    receipt = f"student-{student_id}-{int(time.time())}"
    order: dict[str, Any] = client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
        }
    )
    logger.info("Created Razorpay order %s for student %s (amount=%s)", order.get("id"), student_id, amount)
    return order


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify the `X-Razorpay-Signature` header against the raw request body.

    Uses HMAC-SHA256 keyed with RAZORPAY_WEBHOOK_SECRET, per Razorpay's webhook
    verification spec. Returns False (never raises) on any missing input so
    callers can uniformly reject with 400.
    """
    if not signature or not settings.RAZORPAY_WEBHOOK_SECRET:
        return False
    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
