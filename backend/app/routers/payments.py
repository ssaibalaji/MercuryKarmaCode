"""Payment + Razorpay integration endpoints.

CRITICAL (CLAUDE.md): the webhook endpoint has NO auth dependency. Instead it
verifies the Razorpay webhook signature against the raw request body before
recording anything, and is the only path allowed to mark a Payment `completed`.
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.fee import PaymentResponse, RazorpayOrderRequest, RazorpayOrderResponse
from app.services import fee_service, razorpay_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/razorpay/order", response_model=RazorpayOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_razorpay_order(
    payload: RazorpayOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RazorpayOrderResponse:
    """Create a Razorpay order + pending Payment row. Parent (own child) or teacher (own student)."""
    payment, order = fee_service.create_payment_order(db, current_user, payload.fee_structure_id)
    return RazorpayOrderResponse(
        payment_id=payment.id,
        order_id=order["id"],
        amount=order["amount"],
        currency=order["currency"],
        key_id=settings.RAZORPAY_KEY_ID,
    )


@router.post("/razorpay/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    """Razorpay webhook receiver. Verifies signature before recording any payment.

    No `get_current_user` dependency by design - Razorpay calls this endpoint
    directly, so authentication is the HMAC signature check below, never a
    trusted-by-default client claim.
    """
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not razorpay_service.verify_webhook_signature(body, signature):
        logger.warning("Rejected Razorpay webhook: invalid or missing signature")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    try:
        parsed_payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc

    fee_service.record_payment_from_webhook(db, parsed_payload)
    return {"status": "ok"}


@router.get("/student/{student_id}", response_model=list[PaymentResponse])
async def get_payment_history(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PaymentResponse]:
    """Role-scoped payment history for a student."""
    return fee_service.get_payment_history(db, current_user, student_id)
