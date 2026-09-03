"""Authentication and profile routes."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)

from server.extensions import db, limiter
from server.models.user import User
from server.schemas.auth import LoginSchema, RegisterSchema, UpdateProfileSchema
from server.services.auth_service import AuthService
from server.utils.auth import get_current_authenticated_user, login_required
from server.utils.errors import AuthenticationError, ValidationError

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("3 per minute")
def register():
    """Register a new customer or fundi account."""
    schema = RegisterSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    user, access_token, refresh_token = AuthService.register_user(data)

    response = jsonify(
        {
            "message": "Account created successfully",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response, 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """Authenticate user with email or phone."""
    schema = LoginSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    user, access_token, refresh_token = AuthService.authenticate_user(
        data["email_or_phone"], data["password"]
    )

    response = jsonify(
        {
            "message": "Login successful",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    )
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response, 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Exchange a refresh token for a new access token."""
    user = db.session.get(User, get_jwt_identity())
    if not user or not user.is_active:
        raise AuthenticationError("User account not found or disabled")

    access_token = create_access_token(identity=user.id)
    response = jsonify(
        {
            "message": "Session refreshed",
            "user": user.to_dict(),
            "access_token": access_token,
        }
    )
    set_access_cookies(response, access_token)
    return response, 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Clear session authentication cookies."""
    response = jsonify({"message": "Successfully logged out"})
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_me():
    """Get profile of current logged-in user."""
    user = get_current_authenticated_user()
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["PATCH"])
@login_required
def update_me():
    """Update profile of current user."""
    user = get_current_authenticated_user()
    schema = UpdateProfileSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"]
    if "phone" in data:
        from server.utils.formatters import normalize_phone_number

        user.phone = normalize_phone_number(data["phone"])

    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200
