"""Pytest fixtures and test helpers for Fundi Connect."""

import pytest
from flask_jwt_extended import create_access_token

from server.app import create_app
from server.extensions import db as _db
from server.models.category import Category
from server.models.fundi_profile import FundiProfile, FundiSkill
from server.models.user import User
from server.models.wallet import Wallet


@pytest.fixture(scope="session")
def app():
    """Create test application configured for testing."""
    return create_app("testing")


@pytest.fixture(scope="function", autouse=True)
def app_context(app):
    """Maintain active application context and clean DB for each test."""
    with app.app_context():
        _db.create_all()
        yield
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app_context):
    """Provide database session."""
    return _db


@pytest.fixture(scope="function")
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def sample_category(db):
    """Seed sample plumbing category."""
    cat = Category(
        name="Plumbing & Drainage",
        slug="plumbing",
        description="Plumbing services",
        icon="Wrench",
    )
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture(scope="function")
def sample_customer(db):
    """Create test customer."""
    user = User(
        email="test.customer@example.com",
        phone="254711000111",
        role="customer",
        full_name="Jane Doe",
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    wallet = Wallet(user_id=user.id, balance_cents=0)
    db.session.add(wallet)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def sample_fundi(db, sample_category):
    """Create test verified fundi."""
    user = User(
        email="test.fundi@example.com",
        phone="254722000222",
        role="fundi",
        full_name="Mwangi Fundi",
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    profile = FundiProfile(
        user_id=user.id,
        business_name="Mwangi Fast Fixes",
        bio="Experienced plumber in Nairobi",
        experience_years=5,
        verification_status="verified",
        location_name="Kilimani, Nairobi",
        latitude=-1.2921,
        longitude=36.7845,
        hourly_rate_cents=150000,
        rating_avg=4.9,
        rating_count=10,
        jobs_completed=12,
    )
    db.session.add(profile)
    db.session.flush()

    skill = FundiSkill(
        fundi_profile_id=profile.id,
        category_id=sample_category.id,
        skill_name="Plumbing",
        experience_years=5,
    )
    db.session.add(skill)

    wallet = Wallet(user_id=user.id, balance_cents=500000)  # KES 5,000 balance
    db.session.add(wallet)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def sample_admin(db):
    """Create test admin."""
    user = User(
        email="admin@example.com",
        phone="254700000999",
        role="admin",
        full_name="Platform Admin",
    )
    user.set_password("adminpass123")
    db.session.add(user)
    db.session.flush()

    wallet = Wallet(user_id=user.id, balance_cents=0)
    db.session.add(wallet)
    db.session.commit()
    return user


def auth_header_for(app, user: User) -> dict:
    """Generate Bearer Authorization header for test user."""
    token = create_access_token(identity=user.id)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
