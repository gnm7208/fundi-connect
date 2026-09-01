"""Fundi discovery, search, profile, and verification routes."""

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from server.extensions import db
from server.models.category import Category
from server.models.fundi_profile import FundiProfile, FundiSkill
from server.models.review import Review
from server.models.user import User
from server.schemas.fundi import (
    AddSkillSchema,
    FundiProfileUpdateSchema,
    FundiSearchQuerySchema,
    FundiVerificationSchema,
)
from server.services.geolocation_service import (
    calculate_haversine_distance,
)
from server.utils.auth import (
    fundi_required,
    get_current_authenticated_user,
)
from server.utils.errors import NotFoundError, ValidationError

fundis_bp = Blueprint("fundis", __name__)


@fundis_bp.route("/search", methods=["GET"])
def search_fundis():
    """Discover nearby fundis filtered by location, category, rating, and availability."""
    schema = FundiSearchQuerySchema()
    errors = schema.validate(request.args.to_dict())
    if errors:
        raise ValidationError("Invalid search parameters", payload={"fields": errors})

    params = schema.load(request.args.to_dict())
    query = FundiProfile.query.join(User).filter(User.is_active.is_(True))

    # Category filter
    if params.get("category"):
        cat_id_or_slug = params["category"]
        cat = Category.query.filter(
            or_(Category.id == cat_id_or_slug, Category.slug == cat_id_or_slug)
        ).first()
        if cat:
            query = query.join(FundiSkill).filter(FundiSkill.category_id == cat.id)

    # Verification filter
    if params.get("verified_only"):
        query = query.filter(FundiProfile.verification_status == "verified")

    # Min rating filter
    if params.get("min_rating"):
        query = query.filter(FundiProfile.rating_avg >= params["min_rating"])

    # Text search on business name or user name
    if params.get("q"):
        search_term = f"%{params['q']}%"
        query = query.filter(
            or_(
                FundiProfile.business_name.ilike(search_term),
                FundiProfile.bio.ilike(search_term),
                User.full_name.ilike(search_term),
                FundiProfile.location_name.ilike(search_term),
            )
        )

    profiles = query.all()
    results = []

    user_lat = params.get("lat")
    user_lng = params.get("lng")
    radius_km = params.get("radius_km", 25.0)

    for profile in profiles:
        data = profile.to_dict(include_skills=True)
        data["fundi_name"] = profile.user.full_name if profile.user else None
        data["avatar_url"] = profile.user.avatar_url if profile.user else None

        distance = None
        if user_lat is not None and user_lng is not None:
            if profile.latitude is not None and profile.longitude is not None:
                distance = calculate_haversine_distance(
                    user_lat, user_lng, profile.latitude, profile.longitude
                )
                if distance > radius_km:
                    continue  # Out of desired radius
        data["distance_km"] = distance
        results.append(data)

    # Sorting
    sort_by = params.get("sort", "rating")
    if sort_by == "rating":
        results.sort(key=lambda x: (x["rating_avg"], x["rating_count"]), reverse=True)
    elif sort_by == "distance" and user_lat is not None and user_lng is not None:
        results.sort(
            key=lambda x: x["distance_km"] if x["distance_km"] is not None else float("inf")
        )
    elif sort_by == "jobs":
        results.sort(key=lambda x: x["jobs_completed"], reverse=True)
    elif sort_by == "rate_asc":
        results.sort(key=lambda x: x["hourly_rate_cents"] or float("inf"))
    elif sort_by == "rate_desc":
        results.sort(key=lambda x: x["hourly_rate_cents"] or 0, reverse=True)

    return jsonify({"fundis": results, "count": len(results)}), 200


@fundis_bp.route("/<string:fundi_id>", methods=["GET"])
def get_fundi_detail(fundi_id: str):
    """Retrieve detailed public profile of a fundi."""
    fundi = db.session.get(User, fundi_id)
    if not fundi or not fundi.is_fundi() or not fundi.fundi_profile:
        raise NotFoundError("Fundi not found")

    profile = fundi.fundi_profile
    data = profile.to_dict(include_skills=True)
    data["full_name"] = fundi.full_name
    data["phone"] = fundi.phone
    data["avatar_url"] = fundi.avatar_url

    # Include recent reviews
    reviews = (
        Review.query.filter_by(fundi_id=profile.id)
        .order_by(Review.created_at.desc())
        .limit(10)
        .all()
    )
    data["recent_reviews"] = [r.to_dict() for r in reviews]

    return jsonify({"fundi": data}), 200


@fundis_bp.route("/profile", methods=["PATCH"])
@fundi_required
def update_fundi_profile():
    """Update fundi profile, availability, and pricing."""
    user = get_current_authenticated_user()
    profile = user.fundi_profile
    if not profile:
        raise NotFoundError("Fundi profile not initialized")

    schema = FundiProfileUpdateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    for key, value in data.items():
        if hasattr(profile, key):
            setattr(profile, key, value)

    db.session.commit()
    return jsonify({"message": "Profile updated", "fundi_profile": profile.to_dict()}), 200


@fundis_bp.route("/skills", methods=["POST"])
@fundi_required
def add_skill():
    """Add a trade or skill to fundi profile."""
    user = get_current_authenticated_user()
    profile = user.fundi_profile
    if not profile:
        raise NotFoundError("Fundi profile not found")

    schema = AddSkillSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    category = db.session.get(Category, data["category_id"])
    if not category:
        raise NotFoundError("Category not found")

    skill = FundiSkill(
        fundi_profile_id=profile.id,
        category_id=category.id,
        skill_name=data["skill_name"],
        experience_years=data.get("experience_years", 1),
        certification_url=data.get("certification_url"),
    )
    db.session.add(skill)
    db.session.commit()

    return jsonify({"message": "Skill added", "skill": skill.to_dict()}), 201


@fundis_bp.route("/skills/<string:skill_id>", methods=["DELETE"])
@fundi_required
def delete_skill(skill_id: str):
    """Remove a skill from fundi profile."""
    user = get_current_authenticated_user()
    skill = db.session.get(FundiSkill, skill_id)
    if not skill or skill.fundi_profile_id != user.fundi_profile.id:
        raise NotFoundError("Skill not found")

    db.session.delete(skill)
    db.session.commit()
    return jsonify({"message": "Skill removed"}), 200


@fundis_bp.route("/verify-id", methods=["POST"])
@fundi_required
def submit_verification():
    """Submit national ID and document proof for badge verification."""
    user = get_current_authenticated_user()
    profile = user.fundi_profile
    if not profile:
        raise NotFoundError("Fundi profile not found")

    schema = FundiVerificationSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    profile.id_number = data["id_number"]
    profile.id_document_url = data["id_document_url"]
    profile.verification_status = "pending"
    profile.verification_notes = "Verification submitted for review."

    db.session.commit()
    return (
        jsonify(
            {
                "message": "Verification documents submitted successfully. Admin review in progress.",
                "verification_status": profile.verification_status,
            }
        ),
        200,
    )
