"""Standardized exception classes and error handlers."""

from flask import jsonify


class APIError(Exception):
    """Base API exception with HTTP status code and error message."""

    def __init__(self, message: str, status_code: int = 400, payload: dict | None = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self) -> dict:
        rv = dict(self.payload)
        rv["error"] = self.message
        rv["status_code"] = self.status_code
        return rv


class ValidationError(APIError):
    def __init__(self, message: str, payload: dict | None = None):
        super().__init__(message, status_code=422, payload=payload)


class AuthenticationError(APIError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)


class ForbiddenError(APIError):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class NotFoundError(APIError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(APIError):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class StateTransitionError(APIError):
    def __init__(self, message: str = "Invalid status transition"):
        super().__init__(message, status_code=400)


class EscrowError(APIError):
    def __init__(self, message: str = "Escrow transaction failed"):
        super().__init__(message, status_code=400)


def register_error_handlers(app):
    """Register custom JSON error handlers on Flask application."""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def handle_bad_request(e):
        return jsonify({"error": "Bad request", "status_code": 400}), 400

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"error": "Endpoint or resource not found", "status_code": 404}), 404

    @app.errorhandler(429)
    def handle_ratelimit(e):
        return jsonify(
            {"error": "Rate limit exceeded. Please try again later.", "status_code": 429}
        ), 429

    @app.errorhandler(500)
    def handle_server_error(e):
        return jsonify({"error": "Internal server error", "status_code": 500}), 500
