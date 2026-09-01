"""Booking agreement and lifecycle routes."""

from flask import Blueprint, jsonify, request

from server.extensions import db
from server.models.booking import Booking
from server.schemas.booking import BookingCreateSchema, BookingStatusUpdateSchema
from server.services.booking_service import BookingService
from server.utils.auth import (
    customer_required,
    get_current_authenticated_user,
    login_required,
)
from server.utils.errors import ForbiddenError, NotFoundError, ValidationError
from server.utils.pagination import get_pagination_params, paginate_query

bookings_bp = Blueprint("bookings", __name__)


@bookings_bp.route("", methods=["POST"])
@customer_required
def create_direct_booking():
    """Customer creates a direct booking with a fundi."""
    customer = get_current_authenticated_user()
    schema = BookingCreateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    booking = BookingService.create_booking(customer, data)

    return jsonify({"message": "Booking created", "booking": booking.to_dict()}), 201


@bookings_bp.route("", methods=["GET"])
@login_required
def list_bookings():
    """List bookings for the authenticated customer or fundi."""
    user = get_current_authenticated_user()
    page, per_page = get_pagination_params()

    if user.is_admin():
        query = Booking.query
    elif user.is_fundi():
        query = Booking.query.filter_by(fundi_id=user.id)
    else:
        query = Booking.query.filter_by(customer_id=user.id)

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Booking.created_at.desc())
    paginated = paginate_query(query, page, per_page)

    return (
        jsonify(
            {
                "bookings": [b.to_dict() for b in paginated["items"]],
                "pagination": paginated["pagination"],
            }
        ),
        200,
    )


@bookings_bp.route("/<string:booking_id>", methods=["GET"])
@login_required
def get_booking(booking_id: str):
    """Retrieve detailed booking record."""
    user = get_current_authenticated_user()
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise NotFoundError("Booking not found")

    if not user.is_admin() and user.id not in (booking.customer_id, booking.fundi_id):
        raise ForbiddenError("Access to this booking is unauthorized")

    return jsonify({"booking": booking.to_dict()}), 200


@bookings_bp.route("/<string:booking_id>/status", methods=["PATCH"])
@login_required
def update_booking_status(booking_id: str):
    """Advance booking state machine with RBAC validation."""
    user = get_current_authenticated_user()
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise NotFoundError("Booking not found")

    schema = BookingStatusUpdateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    notes = request.get_json().get("notes")

    updated_booking = BookingService.transition_status(
        booking, data["status"], actor=user, notes=notes
    )

    return (
        jsonify(
            {
                "message": f"Booking status updated to '{updated_booking.status}'",
                "booking": updated_booking.to_dict(),
            }
        ),
        200,
    )


@bookings_bp.route("/<string:booking_id>/confirm", methods=["POST"])
@customer_required
def confirm_job_completion(booking_id: str):
    """Customer verifies satisfactory job completion, auto-releasing escrow."""
    customer = get_current_authenticated_user()
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise NotFoundError("Booking not found")

    if booking.customer_id != customer.id and not customer.is_admin():
        raise ForbiddenError("Only the customer can confirm job completion")

    updated_booking = BookingService.transition_status(booking, "completed", actor=customer)

    return (
        jsonify(
            {
                "message": "Job completion confirmed. Escrow payment released to Fundi wallet!",
                "booking": updated_booking.to_dict(),
            }
        ),
        200,
    )
