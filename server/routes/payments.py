"""M-PESA Daraja payment and webhook callback routes."""

from flask import Blueprint, jsonify, request

from server.extensions import db, limiter
from server.models.booking import Booking
from server.models.escrow import EscrowTransaction
from server.schemas.payment import SimulatePaymentCallbackSchema, STKPushInitiateSchema
from server.services.daraja_service import DarajaService
from server.services.escrow_service import EscrowService
from server.utils.auth import customer_required, get_current_authenticated_user, login_required
from server.utils.errors import ForbiddenError, NotFoundError, ValidationError

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/stk-push", methods=["POST"])
@customer_required
@limiter.limit("10 per minute")
def initiate_stk_push():
    """Trigger Safaricom M-PESA STK Push to deposit funds into Escrow."""
    customer = get_current_authenticated_user()
    schema = STKPushInitiateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    booking = db.session.get(Booking, data["booking_id"])
    if not booking:
        raise NotFoundError("Booking not found")

    if booking.customer_id != customer.id and not customer.is_admin():
        raise ForbiddenError("Only the booking customer can initiate escrow payment")

    if booking.status not in ("pending", "accepted_unpaid"):
        raise ValidationError(f"Cannot deposit escrow for booking in status '{booking.status}'")

    daraja = DarajaService()
    result = daraja.initiate_stk_push(
        phone_number=data["phone_number"],
        amount_cents=booking.agreed_amount_cents,
        booking_id=booking.id,
        description=f"Fundi Connect Escrow: {booking.title}",
    )

    if not result.get("success"):
        return (
            jsonify(
                {
                    "error": "Failed to initiate M-PESA STK Push",
                    "details": result.get("ResponseDescription") or result.get("errorMessage"),
                }
            ),
            400,
        )

    checkout_request_id = result.get("CheckoutRequestID")
    merchant_request_id = result.get("MerchantRequestID")

    escrow = EscrowService.record_stk_push_initiated(
        booking=booking,
        phone_number=data["phone_number"],
        merchant_request_id=merchant_request_id,
        checkout_request_id=checkout_request_id,
    )

    return (
        jsonify(
            {
                "message": "M-PESA STK Push prompt sent to your phone. Enter your M-PESA PIN to complete deposit.",
                "checkout_request_id": checkout_request_id,
                "amount_kes": booking.agreed_amount_cents / 100,
                "escrow": escrow.to_dict(),
            }
        ),
        200,
    )


@payments_bp.route("/daraja/callback", methods=["POST"])
def daraja_callback():
    """Safaricom Daraja C2B STK Push webhook callback."""
    payload = request.get_json() or {}
    stk_callback = payload.get("Body", {}).get("stkCallback", {})

    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")

    if not checkout_request_id:
        return jsonify({"ResultCode": 1, "ResultDesc": "Rejected: Missing CheckoutRequestID"}), 400

    if result_code == 0:
        # Successful payment
        items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        mpesa_receipt = None
        for item in items:
            name = item.get("Name")
            if name == "MpesaReceiptNumber":
                mpesa_receipt = item.get("Value")

        receipt_str = str(mpesa_receipt or f"REC-{checkout_request_id[:8]}")
        EscrowService.process_successful_payment(
            checkout_request_id=checkout_request_id,
            mpesa_receipt_number=receipt_str,
        )
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted and escrow funded"}), 200
    else:
        # User cancelled or payment failed
        escrow = EscrowTransaction.query.filter_by(checkout_request_id=checkout_request_id).first()
        if escrow and escrow.status == "pending":
            escrow.status = "failed"
            db.session.commit()
        return jsonify(
            {"ResultCode": 0, "ResultDesc": f"Payment failure acknowledged: {result_desc}"}
        ), 200


@payments_bp.route("/simulate-callback", methods=["POST"])
def simulate_callback():
    """Simulate successful M-PESA payment callback (for sandbox/testing/demo)."""
    schema = SimulatePaymentCallbackSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    checkout_id = data["checkout_request_id"]
    receipt = data.get("mpesa_receipt_number") or f"NLJ{checkout_id[-8:].upper()}"

    escrow = EscrowService.process_successful_payment(
        checkout_request_id=checkout_id,
        mpesa_receipt_number=receipt,
    )

    return (
        jsonify(
            {
                "message": "Payment simulation processed. Funds are now held in escrow.",
                "escrow": escrow.to_dict(),
                "booking_status": escrow.booking.status if escrow.booking else None,
            }
        ),
        200,
    )


@payments_bp.route("/status/<string:checkout_request_id>", methods=["GET"])
@login_required
def get_payment_status(checkout_request_id: str):
    """Check status of an STK push transaction."""
    escrow = EscrowTransaction.query.filter_by(checkout_request_id=checkout_request_id).first()
    if not escrow:
        raise NotFoundError("Transaction not found")

    return jsonify({"escrow": escrow.to_dict()}), 200
