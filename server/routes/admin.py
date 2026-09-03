"""Administrator management, metrics, and verification arbitration routes."""

from datetime import UTC, datetime

from flask import Blueprint, jsonify, request

from server.extensions import db
from server.models.booking import Booking
from server.models.dispute import Dispute
from server.models.escrow import EscrowTransaction
from server.models.fundi_profile import FundiProfile
from server.models.notification import Notification
from server.models.user import User
from server.schemas.dispute import DisputeResolveSchema
from server.services.escrow_service import EscrowService
from server.utils.auth import admin_required, get_current_authenticated_user
from server.utils.errors import NotFoundError, ValidationError

admin_bp = Blueprint("admin", __name__)


def utc_now():
    return datetime.now(UTC)


@admin_bp.route("/metrics", methods=["GET"])
@admin_required
def get_metrics():
    """Retrieve platform aggregate statistics, escrow totals, and GMV."""
    total_users = User.query.count()
    total_customers = User.query.filter_by(role="customer").count()
    total_fundis = User.query.filter_by(role="fundi").count()
    verified_fundis = FundiProfile.query.filter_by(verification_status="verified").count()
    pending_verifications = FundiProfile.query.filter_by(verification_status="pending").count()

    total_bookings = Booking.query.count()
    completed_bookings = Booking.query.filter_by(status="completed").count()
    open_disputes = Dispute.query.filter(Dispute.status.in_(["open", "under_review"])).count()

    # Escrow and GMV
    escrow_held = EscrowTransaction.query.filter_by(status="held_in_escrow").all()
    escrow_released = EscrowTransaction.query.filter_by(status="released").all()

    total_held_cents = sum(e.amount_cents for e in escrow_held)
    total_gmv_cents = sum(e.amount_cents for e in escrow_released)
    total_revenue_cents = sum(e.platform_fee_cents for e in escrow_released)

    return (
        jsonify(
            {
                "users": {
                    "total": total_users,
                    "customers": total_customers,
                    "fundis": total_fundis,
                    "verified_fundis": verified_fundis,
                    "pending_verifications": pending_verifications,
                },
                "bookings": {
                    "total": total_bookings,
                    "completed": completed_bookings,
                    "open_disputes": open_disputes,
                },
                "financials": {
                    "total_gmv_kes": total_gmv_cents / 100,
                    "total_revenue_commission_kes": total_revenue_cents / 100,
                    "funds_held_in_escrow_kes": total_held_cents / 100,
                },
            }
        ),
        200,
    )


@admin_bp.route("/fundis/pending-verification", methods=["GET"])
@admin_required
def get_pending_verifications():
    """List fundis awaiting ID verification review."""
    pending = FundiProfile.query.filter_by(verification_status="pending").all()
    results = []
    for p in pending:
        # Admins are reviewing the ID itself, so they get the private fields.
        d = p.to_dict(include_skills=True, include_private=True)
        d["user_name"] = p.user.full_name if p.user else None
        d["email"] = p.user.email if p.user else None
        d["phone"] = p.user.phone if p.user else None
        results.append(d)

    return jsonify({"pending_fundis": results, "count": len(results)}), 200


@admin_bp.route("/fundis/<string:fundi_id>/verify", methods=["PATCH"])
@admin_required
def review_fundi_verification(fundi_id: str):
    """Approve or reject fundi ID badge verification."""
    data = request.get_json() or {}
    status = data.get("status")  # verified or rejected
    if status not in ("verified", "rejected"):
        raise ValidationError("Status must be 'verified' or 'rejected'")

    profile = FundiProfile.query.filter(
        (FundiProfile.id == fundi_id) | (FundiProfile.user_id == fundi_id)
    ).first()
    if not profile:
        raise NotFoundError("Fundi profile not found")

    profile.verification_status = status
    profile.verification_notes = data.get("notes")
    if status == "verified":
        profile.verified_at = utc_now()

    # Notify fundi
    msg = (
        "Congratulations! Your Fundi Connect account has been verified."
        if status == "verified"
        else f"Your verification request was not approved: {data.get('notes', 'Please contact support')}"
    )
    n = Notification(
        user_id=profile.user_id,
        title=f"Verification {status.capitalize()}",
        message=msg,
        type="system",
    )
    db.session.add(n)
    db.session.commit()

    return (
        jsonify(
            {
                "message": f"Fundi verification updated to '{status}'",
                "fundi_profile": profile.to_dict(),
            }
        ),
        200,
    )


@admin_bp.route("/disputes", methods=["GET"])
@admin_required
def get_all_disputes():
    """List all open and resolved disputes."""
    disputes = Dispute.query.order_by(Dispute.created_at.desc()).all()
    return jsonify({"disputes": [d.to_dict() for d in disputes]}), 200


@admin_bp.route("/disputes/<string:dispute_id>/resolve", methods=["POST"])
@admin_required
def resolve_dispute(dispute_id: str):
    """Arbitrate dispute and release or refund escrow funds."""
    admin = get_current_authenticated_user()
    dispute = db.session.get(Dispute, dispute_id)
    if not dispute:
        raise NotFoundError("Dispute not found")

    schema = DisputeResolveSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    action = data["action"]  # refund_customer or payout_fundi
    resolution_text = data["resolution"]

    booking = dispute.booking
    dispute.resolution = resolution_text
    dispute.resolved_by_id = admin.id
    dispute.resolved_at = utc_now()

    if action == "refund_customer":
        dispute.status = "resolved_refund"
        if booking.escrow_transaction and booking.escrow_transaction.status in (
            "held_in_escrow",
            "disputed",
        ):
            EscrowService.refund_escrow_to_customer(
                booking, reason=f"Dispute resolved in customer favor: {resolution_text}"
            )
    elif action == "payout_fundi":
        dispute.status = "resolved_payout"
        if booking.escrow_transaction and booking.escrow_transaction.status in (
            "held_in_escrow",
            "disputed",
        ):
            EscrowService.release_escrow_to_fundi(booking, released_by=admin)

    db.session.commit()
    return (
        jsonify(
            {
                "message": f"Dispute resolved with action '{action}'.",
                "dispute": dispute.to_dict(),
            }
        ),
        200,
    )
