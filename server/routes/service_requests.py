"""Customer service requests and fundi quoting routes."""

from flask import Blueprint, jsonify, request

from server.extensions import db
from server.models.booking import Booking
from server.models.category import Category
from server.models.notification import Notification
from server.models.service_request import Quote, ServiceRequest
from server.schemas.service_request import QuoteCreateSchema, ServiceRequestCreateSchema
from server.services.escrow_service import EscrowService
from server.utils.auth import (
    customer_required,
    fundi_required,
    get_current_authenticated_user,
)
from server.utils.errors import ConflictError, NotFoundError, ValidationError
from server.utils.pagination import get_pagination_params, paginate_query

service_requests_bp = Blueprint("service_requests", __name__)


@service_requests_bp.route("", methods=["POST"])
@customer_required
def create_service_request():
    """Create a new service request / RFQ."""
    customer = get_current_authenticated_user()
    schema = ServiceRequestCreateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    category = db.session.get(Category, data["category_id"])
    if not category:
        raise NotFoundError("Selected category not found")

    sr = ServiceRequest(
        customer_id=customer.id,
        category_id=category.id,
        title=data["title"],
        description=data["description"],
        location_name=data["location_name"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        budget_min_cents=data.get("budget_min_cents"),
        budget_max_cents=data.get("budget_max_cents"),
        preferred_date=data.get("preferred_date"),
        status="open",
    )
    db.session.add(sr)
    db.session.commit()

    return jsonify({"message": "Service request created", "service_request": sr.to_dict()}), 201


@service_requests_bp.route("", methods=["GET"])
def list_service_requests():
    """List open service requests with optional category and status filtering."""
    page, per_page = get_pagination_params()
    query = ServiceRequest.query

    category_id = request.args.get("category_id")
    if category_id:
        query = query.filter_by(category_id=category_id)

    status = request.args.get("status", "open")
    if status != "all":
        query = query.filter_by(status=status)

    query = query.order_by(ServiceRequest.created_at.desc())
    paginated = paginate_query(query, page, per_page)

    return (
        jsonify(
            {
                "service_requests": [sr.to_dict() for sr in paginated["items"]],
                "pagination": paginated["pagination"],
            }
        ),
        200,
    )


@service_requests_bp.route("/<string:sr_id>", methods=["GET"])
def get_service_request_detail(sr_id: str):
    """Get service request details and quotes."""
    sr = db.session.get(ServiceRequest, sr_id)
    if not sr:
        raise NotFoundError("Service request not found")

    # If logged in user is the owner, include all quotes
    return jsonify({"service_request": sr.to_dict(include_quotes=True)}), 200


@service_requests_bp.route("/<string:sr_id>/quotes", methods=["POST"])
@fundi_required
def submit_quote(sr_id: str):
    """Fundi submits a price quote for a service request."""
    fundi = get_current_authenticated_user()
    sr = db.session.get(ServiceRequest, sr_id)
    if not sr:
        raise NotFoundError("Service request not found")

    if sr.status != "open":
        raise ValidationError("This service request is no longer open for quotes")

    existing_quote = Quote.query.filter_by(service_request_id=sr.id, fundi_id=fundi.id).first()
    if existing_quote:
        raise ConflictError("You have already submitted a quote for this request")

    schema = QuoteCreateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    quote = Quote(
        service_request_id=sr.id,
        fundi_id=fundi.id,
        amount_cents=data["amount_cents"],
        estimated_hours=data.get("estimated_hours"),
        notes=data.get("notes"),
        status="pending",
    )
    db.session.add(quote)

    # Notify customer
    n = Notification(
        user_id=sr.customer_id,
        title="New Quote Received",
        message=f"{fundi.full_name} submitted a quote of KES {quote.amount_cents / 100:,.2f} for '{sr.title}'.",
        type="booking",
    )
    db.session.add(n)
    db.session.commit()

    return jsonify({"message": "Quote submitted", "quote": quote.to_dict()}), 201


@service_requests_bp.route("/<string:sr_id>/quotes/<string:quote_id>/accept", methods=["POST"])
@customer_required
def accept_quote(sr_id: str, quote_id: str):
    """Customer accepts a quote, automatically creating a booking and escrow transaction."""
    customer = get_current_authenticated_user()
    sr = db.session.get(ServiceRequest, sr_id)
    if not sr or sr.customer_id != customer.id:
        raise NotFoundError("Service request not found")

    quote = db.session.get(Quote, quote_id)
    if not quote or quote.service_request_id != sr.id:
        raise NotFoundError("Quote not found")

    if sr.status != "open":
        raise ValidationError("Service request is already matched or closed")

    # 1. Update quote and request status
    quote.status = "accepted"
    sr.status = "matched"

    # Decline other pending quotes
    for other in sr.quotes:
        if other.id != quote.id and other.status == "pending":
            other.status = "declined"

    # 2. Create Booking
    platform_fee, fundi_payout = EscrowService.calculate_breakdown(quote.amount_cents)
    booking = Booking(
        customer_id=customer.id,
        fundi_id=quote.fundi_id,
        service_request_id=sr.id,
        title=sr.title,
        description=sr.description,
        agreed_amount_cents=quote.amount_cents,
        platform_fee_cents=platform_fee,
        fundi_amount_cents=fundi_payout,
        location_name=sr.location_name,
        latitude=sr.latitude,
        longitude=sr.longitude,
        scheduled_for=sr.preferred_date,
        status="accepted_unpaid",
    )
    db.session.add(booking)
    db.session.flush()

    # 3. Create EscrowTransaction
    EscrowService.create_or_get_escrow(booking)

    # 4. Notify fundi
    n = Notification(
        user_id=quote.fundi_id,
        title="Quote Accepted!",
        message=f"{customer.full_name} accepted your quote of KES {quote.amount_cents / 100:,.2f} for '{sr.title}'. Awaiting escrow deposit.",
        type="booking",
    )
    db.session.add(n)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Quote accepted and booking created. Please proceed to escrow funding.",
                "booking": booking.to_dict(),
            }
        ),
        201,
    )
