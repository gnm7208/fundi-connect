"""Tests for authentication and user account management."""

from server.tests.conftest import auth_header_for


def test_register_customer_success(client, db):
    """Test successful customer registration."""
    payload = {
        "email": "new.customer@gmail.com",
        "phone": "0712345678",
        "password": "strongPassword123",
        "full_name": "Daniel Kiprono",
        "role": "customer",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["user"]["email"] == "new.customer@gmail.com"
    assert data["user"]["phone"] == "254712345678"  # normalized
    assert data["user"]["role"] == "customer"
    assert "access_token" in data


def test_register_fundi_success(client, db):
    """Test successful fundi registration with profile creation."""
    payload = {
        "email": "new.fundi@gmail.com",
        "phone": "0722998877",
        "password": "fundiPassword123",
        "full_name": "Joseph Mutua",
        "role": "fundi",
        "business_name": "Mutua Electricals",
        "location_name": "Westlands",
        "hourly_rate_cents": 200000,
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["user"]["role"] == "fundi"
    assert data["user"]["fundi_profile"]["business_name"] == "Mutua Electricals"
    assert data["user"]["fundi_profile"]["verification_status"] == "pending"


def test_register_duplicate_email_conflict(client, sample_customer):
    """Duplicate email registration is rejected with 409 conflict."""
    payload = {
        "email": sample_customer.email,
        "phone": "0799887766",
        "password": "somePassword123",
        "full_name": "Duplicate User",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409
    assert "already exists" in res.get_json()["error"]


def test_login_success_with_email_and_phone(client, sample_customer):
    """Test login via email and via phone."""
    # Via email
    res_email = client.post(
        "/api/v1/auth/login",
        json={"email_or_phone": sample_customer.email, "password": "password123"},
    )
    assert res_email.status_code == 200
    assert "access_token" in res_email.get_json()

    # Via normalized phone (0711000111)
    res_phone = client.post(
        "/api/v1/auth/login",
        json={"email_or_phone": "0711000111", "password": "password123"},
    )
    assert res_phone.status_code == 200
    assert "access_token" in res_phone.get_json()


def test_login_invalid_password(client, sample_customer):
    """Invalid credentials return 401 error."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email_or_phone": sample_customer.email, "password": "wrongpassword"},
    )
    assert res.status_code == 401


def test_get_me_authenticated_vs_unauthenticated(app, client, sample_customer):
    """Test GET /api/v1/auth/me requires valid token."""
    # Unauthenticated
    res_unauth = client.get("/api/v1/auth/me")
    assert res_unauth.status_code == 401

    # Authenticated
    headers = auth_header_for(app, sample_customer)
    res_auth = client.get("/api/v1/auth/me", headers=headers)
    assert res_auth.status_code == 200
    assert res_auth.get_json()["user"]["email"] == sample_customer.email
