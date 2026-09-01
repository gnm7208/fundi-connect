"""Flask application factory for Fundi Connect."""

import os

from flask import Flask, jsonify
from sqlalchemy import text

from server.config import config_by_name
from server.extensions import cors, db, jwt, limiter, talisman
from server.routes import register_blueprints
from server.utils.errors import register_error_handlers


def create_app(config_name: str | None = None) -> Flask:
    """Application factory for Fundi Connect API."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)

    # CORS
    cors.init_app(
        app,
        origins=app.config.get("CORS_ORIGINS", ["*"]),
        supports_credentials=True,
    )

    # Limiter
    limiter.init_app(app)

    # Talisman (Security Headers)
    if not app.config.get("TESTING") and not app.config.get("DEBUG"):
        talisman.init_app(
            app,
            force_https=False,  # Let reverse proxy (Render/Vercel/Nginx) handle SSL termination
            content_security_policy=None,
        )

    # Register Error Handlers
    register_error_handlers(app)

    # Register Blueprints
    register_blueprints(app)

    # Health Check Endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint verifying application and database status."""
        db_status = "healthy"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        return (
            jsonify(
                {
                    "status": "online",
                    "service": "Fundi Connect API",
                    "version": "0.1.0",
                    "database": db_status,
                    "environment": config_name,
                }
            ),
            200 if "unhealthy" not in db_status else 503,
        )

    # Automatically create tables in SQLite development/testing modes
    with app.app_context():
        if app.config.get("TESTING") or "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
            db.create_all()

    return app
