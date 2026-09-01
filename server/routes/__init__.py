"""Routes export and blueprint registration package."""

from flask import Blueprint

from server.routes.admin import admin_bp
from server.routes.auth import auth_bp
from server.routes.bookings import bookings_bp
from server.routes.categories import categories_bp
from server.routes.conversations import conversations_bp
from server.routes.disputes import disputes_bp
from server.routes.escrow import escrow_bp
from server.routes.fundis import fundis_bp
from server.routes.payments import payments_bp
from server.routes.reviews import reviews_bp
from server.routes.service_requests import service_requests_bp
from server.routes.wallets import wallets_bp

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def register_blueprints(app):
    """Register all domain blueprints under /api/v1."""
    api_v1_bp.register_blueprint(auth_bp, url_prefix="/auth")
    api_v1_bp.register_blueprint(fundis_bp, url_prefix="/fundis")
    api_v1_bp.register_blueprint(categories_bp, url_prefix="/categories")
    api_v1_bp.register_blueprint(service_requests_bp, url_prefix="/service-requests")
    api_v1_bp.register_blueprint(bookings_bp, url_prefix="/bookings")
    api_v1_bp.register_blueprint(payments_bp, url_prefix="/payments")
    api_v1_bp.register_blueprint(escrow_bp, url_prefix="/escrow")
    api_v1_bp.register_blueprint(reviews_bp, url_prefix="/reviews")
    api_v1_bp.register_blueprint(disputes_bp, url_prefix="/disputes")
    api_v1_bp.register_blueprint(wallets_bp, url_prefix="/wallets")
    api_v1_bp.register_blueprint(conversations_bp, url_prefix="/conversations")
    api_v1_bp.register_blueprint(admin_bp, url_prefix="/admin")

    app.register_blueprint(api_v1_bp)
