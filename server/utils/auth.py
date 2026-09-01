"""Authentication and RBAC decorators."""

from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from server.extensions import db
from server.models.user import User
from server.utils.errors import AuthenticationError, ForbiddenError


def get_current_authenticated_user() -> User:
    """Fetch current user from JWT identity."""
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    if not user_id:
        raise AuthenticationError("Invalid or expired session")

    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User account not found or disabled")

    g.current_user = user
    return user


def login_required(fn):
    """Ensure request is authenticated with a valid user."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        get_current_authenticated_user()
        return fn(*args, **kwargs)

    return wrapper


def customer_required(fn):
    """Ensure user has 'customer' or 'admin' role."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_authenticated_user()
        if user.role not in ("customer", "admin"):
            raise ForbiddenError("Customer access required for this action")
        return fn(*args, **kwargs)

    return wrapper


def fundi_required(fn):
    """Ensure user has 'fundi' or 'admin' role."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_authenticated_user()
        if user.role not in ("fundi", "admin"):
            raise ForbiddenError("Fundi service provider access required")
        return fn(*args, **kwargs)

    return wrapper


def verified_fundi_required(fn):
    """Ensure user is a verified fundi or admin."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_authenticated_user()
        if user.is_admin():
            return fn(*args, **kwargs)

        if not user.is_fundi() or not user.fundi_profile:
            raise ForbiddenError("Fundi profile required")

        if user.fundi_profile.verification_status != "verified":
            raise ForbiddenError(
                "Your account is pending verification. Verified fundi status required."
            )
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    """Ensure user has 'admin' role."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_authenticated_user()
        if not user.is_admin():
            raise ForbiddenError("Admin credentials required")
        return fn(*args, **kwargs)

    return wrapper
