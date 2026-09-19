"""Application configuration classes for Fundi Connect."""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration with sensible defaults."""

    SECRET_KEY = os.getenv(
        "SECRET_KEY", "dev-fallback-secret-fundi-connect-2026-very-secure-key-32bytes"
    )

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///fundi_connect_dev.db")
    # Fix postgres:// URL prefix if provided (e.g. by Render/Neon)
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    # JWT Settings
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "dev-jwt-fallback-secret-2026-fundi-connect-marketplace-key"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))
    )
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SECURE = False  # Set to True in production
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = False  # Keep simple for API/mobile usage

    # CORS
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,https://fundi-connect-pi.vercel.app",
        ).split(",")
        if origin.strip()
    ]

    # Rate Limiting
    RATELIMIT_DEFAULT = "100 per minute"
    RATELIMIT_STORAGE_URI = "memory://"

    # Platform Business Rules
    # Held as integer basis points so no commission calculation ever touches a float.
    PLATFORM_COMMISSION_BPS = int(
        round(float(os.getenv("PLATFORM_COMMISSION_PERCENT", "10.0")) * 100)
    )

    # Daraja M-PESA
    DARAJA_ENVIRONMENT = os.getenv("DARAJA_ENVIRONMENT", "sandbox")
    DARAJA_CONSUMER_KEY = os.getenv("DARAJA_CONSUMER_KEY", "mock_consumer_key")
    DARAJA_CONSUMER_SECRET = os.getenv("DARAJA_CONSUMER_SECRET", "mock_consumer_secret")
    DARAJA_PASSKEY = os.getenv(
        "DARAJA_PASSKEY",
        "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919",
    )
    DARAJA_SHORTCODE = os.getenv("DARAJA_SHORTCODE", "174379")
    DARAJA_CALLBACK_URL = os.getenv(
        "DARAJA_CALLBACK_URL",
        "https://fundi-connect-api.onrender.com/api/v1/payments/daraja/callback",
    )
    DARAJA_SIMULATION_MODE = os.getenv("DARAJA_SIMULATION_MODE", "true").lower() in (
        "true",
        "1",
        "yes",
    )
    # Escape hatch for a public demo deployment: lets simulated payments run under
    # FLASK_ENV=production, where they are otherwise refused. Never set this on an
    # instance handling real customer money — it makes escrow fundable for free.
    ALLOW_SIMULATED_PAYMENTS = os.getenv("ALLOW_SIMULATED_PAYMENTS", "false").lower() in (
        "true",
        "1",
        "yes",
    )


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_COOKIE_SECURE = False
    DARAJA_SIMULATION_MODE = True
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Strict"

    @classmethod
    def validate(cls):
        """Validate critical production environment variables."""
        required = ["SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL"]
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            raise ValueError(
                f"Missing required production environment variables: {', '.join(missing)}"
            )

        if cls.DARAJA_SIMULATION_MODE and not cls.ALLOW_SIMULATED_PAYMENTS:
            raise ValueError(
                "DARAJA_SIMULATION_MODE must be disabled in production: simulated "
                "payments would let customers fund escrow without paying. Set "
                "ALLOW_SIMULATED_PAYMENTS=true only for a demo instance holding no real money."
            )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
