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

    if hasattr(config_class, "validate"):
        config_class.validate()

    if app.config.get("DARAJA_SIMULATION_MODE") and app.config.get("ALLOW_SIMULATED_PAYMENTS"):
        app.logger.warning(
            "Running with SIMULATED M-PESA payments in a production environment. "
            "Escrow can be funded without any money moving. Demo instances only."
        )

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
                    # Stated plainly so a demo instance never looks like it moves real money.
                    "payments": "simulated" if app.config.get("DARAJA_SIMULATION_MODE") else "live",
                }
            ),
            200 if "unhealthy" not in db_status else 503,
        )

    @app.cli.command("init-db")
    def init_db_command():
        """Create any missing tables.

        Stands in for Alembic until migrations exist: it is idempotent, so it is safe
        to run on every deploy, but it will not alter columns on an existing table.
        """
        db.create_all()
        print("Database tables are up to date.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Populate an empty database with demo data.

        Refuses to touch a database that already has users, so it is safe to leave
        in a hosted start command where free-tier plans offer no shell access.
        """
        from server.models.user import User
        from server.seed import seed_database

        if db.session.query(User.id).first() is not None:
            print("Database already has users — skipping demo seed.")
            return

        seed_database(app=app, reset=False)

    # Automatically create tables in SQLite development/testing modes
    with app.app_context():
        if app.config.get("TESTING") or "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
            db.create_all()

    return app
