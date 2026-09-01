"""Verified customer review routes."""

from flask import Blueprint, jsonify, request

from server.models.fundi_profile import FundiProfile
from server.models.review import Review
from server.schemas.review import ReviewCreateSchema
from server.services.review_service import ReviewService
from server.utils.auth import customer_required, get_current_authenticated_user
from server.utils.errors import NotFoundError, ValidationError
from server.utils.pagination import get_pagination_params, paginate_query

reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.route("", methods=["POST"])
@customer_required
def create_review():
    """Submit a verified rating and review for a completed job booking."""
    customer = get_current_authenticated_user()
    schema = ReviewCreateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    review = ReviewService.create_review(
        customer=customer,
        booking_id=data["booking_id"],
        rating=data["rating"],
        review_text=data.get("review_text"),
    )

    return (
        jsonify(
            {
                "message": "Review submitted successfully. Thank you for rating your fundi!",
                "review": review.to_dict(),
            }
        ),
        201,
    )


@reviews_bp.route("/fundi/<string:fundi_id>", methods=["GET"])
def get_fundi_reviews(fundi_id: str):
    """List verified reviews for a specific fundi profile."""
    profile = FundiProfile.query.filter(
        (FundiProfile.id == fundi_id) | (FundiProfile.user_id == fundi_id)
    ).first()
    if not profile:
        raise NotFoundError("Fundi not found")

    page, per_page = get_pagination_params()
    query = Review.query.filter_by(fundi_id=profile.id).order_by(Review.created_at.desc())
    paginated = paginate_query(query, page, per_page)

    return (
        jsonify(
            {
                "reviews": [r.to_dict() for r in paginated["items"]],
                "rating_avg": profile.rating_avg,
                "rating_count": profile.rating_count,
                "pagination": paginated["pagination"],
            }
        ),
        200,
    )
