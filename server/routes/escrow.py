"""Escrow tracking and ledger inspection routes."""

from flask import Blueprint, jsonify

from server.extensions import db
from server.models.booking import Booking
from server.models.escrow import EscrowTransaction
from server.utils.auth import admin_required, get_current_authenticated_user, login_required
from server.utils.errors import ForbiddenError, NotFoundError

escrow_bp = Blueprint("escrow", __name__)


@escrow_bp.route("/booking/<string:booking_id>", methods=["GET"])
@login_required
def get_booking_escrow(booking_id: str):
    """Retrieve escrow transaction status and breakdown for a booking."""
    user = get_current_authenticated_user()
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise NotFoundError("Booking not found")

    if not user.is_admin() and user.id not in (booking.customer_id, booking.fundi_id):
        raise ForbiddenError("Unauthorized access to booking escrow details")

    escrow = booking.escrow_transaction
    if not escrow:
        raise NotFoundError("No escrow record exists for this booking")

    return jsonify({"escrow": escrow.to_dict()}), 200


@escrow_bp.route("/summary", methods=["GET"])
@admin_required
def get_escrow_summary():
    """Admin summary of all funds held in escrow across the platform."""
    held = EscrowTransaction.query.filter_by(status="held_in_escrow").all()
    total_held_cents = sum(e.amount_cents for e in held)
    total_fee_cents = sum(e.platform_fee_cents for e in held)

    released = EscrowTransaction.query.filter_by(status="released").all()
    total_released_cents = sum(e.amount_cents for e in released)
    total_earned_commission_cents = sum(e.platform_fee_cents for e in released)

    return (
        jsonify(
            {
                "held_in_escrow_count": len(held),
                "total_held_kes": total_held_cents / 100,
                "projected_commission_kes": total_fee_cents / 100,
                "total_completed_volume_kes": total_released_cents / 100,
                "total_earned_commission_kes": total_earned_commission_cents / 100,
            }
        ),
        200,
    )
