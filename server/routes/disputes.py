"""Dispute management and arbitration routes."""

from datetime import UTC, datetime

from flask import Blueprint, jsonify, request

from server.extensions import db
from server.models.booking import Booking
from server.models.dispute import Dispute
from server.models.notification import Notification
from server.schemas.dispute import DisputeCreateSchema, DisputeResponseSchema
from server.utils.auth import get_current_authenticated_user, login_required
from server.utils.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError

disputes_bp = Blueprint("disputes", __name__)


def utc_now():
    return datetime.now(UTC)


@disputes_bp.route("", methods=["POST"])
@login_required
def file_dispute():
    """File a dispute regarding a booking."""
    user = get_current_authenticated_user()
    schema = DisputeCreateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    booking = db.session.get(Booking, data["booking_id"])
    if not booking:
        raise NotFoundError("Booking not found")

    if user.id not in (booking.customer_id, booking.fundi_id) and not user.is_admin():
        raise ForbiddenError("Only participants in this booking can file a dispute")

    if booking.dispute:
        raise ConflictError("A dispute has already been filed for this booking")

    dispute = Dispute(
        booking_id=booking.id,
        initiated_by_id=user.id,
        reason=data["reason"],
        customer_statement=data["customer_statement"],
        status="open",
    )
    booking.status = "disputed"
    if booking.escrow_transaction:
        booking.escrow_transaction.status = "disputed"

    db.session.add(dispute)

    # Notify counterparty
    counterparty_id = booking.fundi_id if user.id == booking.customer_id else booking.customer_id
    n = Notification(
        user_id=counterparty_id,
        title="Dispute Filed on Booking",
        message=f"A dispute has been opened for '{booking.title}': {dispute.reason}. Please provide your statement.",
        type="dispute",
    )
    db.session.add(n)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Dispute opened. Funds remain secured in escrow pending resolution.",
                "dispute": dispute.to_dict(),
            }
        ),
        201,
    )


@disputes_bp.route("/<string:dispute_id>", methods=["GET"])
@login_required
def get_dispute(dispute_id: str):
    """Retrieve dispute details."""
    user = get_current_authenticated_user()
    dispute = db.session.get(Dispute, dispute_id)
    if not dispute:
        raise NotFoundError("Dispute not found")

    booking = dispute.booking
    if not user.is_admin() and user.id not in (booking.customer_id, booking.fundi_id):
        raise ForbiddenError("Unauthorized access to dispute")

    return jsonify({"dispute": dispute.to_dict()}), 200


@disputes_bp.route("/<string:dispute_id>/respond", methods=["POST"])
@login_required
def respond_to_dispute(dispute_id: str):
    """Counterparty provides their statement for dispute review."""
    user = get_current_authenticated_user()
    dispute = db.session.get(Dispute, dispute_id)
    if not dispute:
        raise NotFoundError("Dispute not found")

    booking = dispute.booking
    if user.id not in (booking.customer_id, booking.fundi_id) and not user.is_admin():
        raise ForbiddenError("Unauthorized to respond to this dispute")

    schema = DisputeResponseSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    dispute.fundi_statement = data["fundi_statement"]
    dispute.status = "under_review"
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Statement submitted. Admin review in progress.",
                "dispute": dispute.to_dict(),
            }
        ),
        200,
    )
