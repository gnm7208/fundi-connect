"""Tests for the production configuration guards."""

import pytest

from server.config import ProductionConfig


def _production_env(monkeypatch, **overrides):
    """Set the minimum env a production boot requires, plus any overrides."""
    base = {
        "SECRET_KEY": "prod-secret",
        "JWT_SECRET_KEY": "prod-jwt-secret",
        "DATABASE_URL": "postgresql://user:pass@localhost/fundi",
    }
    for key, value in {**base, **overrides}.items():
        monkeypatch.setenv(key, value)


def test_production_requires_real_secrets(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("JWT_SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/fundi")

    with pytest.raises(ValueError, match="SECRET_KEY"):
        ProductionConfig.validate()


def test_production_refuses_simulated_payments(monkeypatch):
    """A live instance must never accept payments that move no money."""
    _production_env(monkeypatch)
    monkeypatch.setattr(ProductionConfig, "DARAJA_SIMULATION_MODE", True)
    monkeypatch.setattr(ProductionConfig, "ALLOW_SIMULATED_PAYMENTS", False)

    with pytest.raises(ValueError, match="DARAJA_SIMULATION_MODE"):
        ProductionConfig.validate()


def test_demo_instances_may_opt_into_simulated_payments(monkeypatch):
    """The public demo deployment opts in explicitly and is allowed to boot."""
    _production_env(monkeypatch)
    monkeypatch.setattr(ProductionConfig, "DARAJA_SIMULATION_MODE", True)
    monkeypatch.setattr(ProductionConfig, "ALLOW_SIMULATED_PAYMENTS", True)

    ProductionConfig.validate()  # must not raise


def test_live_payments_pass_validation(monkeypatch):
    _production_env(monkeypatch)
    monkeypatch.setattr(ProductionConfig, "DARAJA_SIMULATION_MODE", False)
    monkeypatch.setattr(ProductionConfig, "ALLOW_SIMULATED_PAYMENTS", False)

    ProductionConfig.validate()  # must not raise
