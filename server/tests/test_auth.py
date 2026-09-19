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


def _booking(db, customer, fundi, status):
    from server.models.booking import Booking

    booking = Booking(
        customer_id=customer.id,
        fundi_id=fundi.id,
        title="Kitchen tap",
        agreed_amount_cents=150000,
        location_name="Kilimani",
        status=status,
    )
    db.session.add(booking)
    db.session.commit()
    return booking


def test_delete_account_rejects_wrong_password_with_403(app, client, sample_customer):
    """403, not 401 — the client treats a 401 as an expired session and signs out."""
    headers = auth_header_for(app, sample_customer)
    res = client.delete("/api/v1/auth/me", json={"password": "nope"}, headers=headers)
    assert res.status_code == 403
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200


def test_delete_account_refuses_while_a_job_is_active(
    app, client, db, sample_customer, sample_fundi
):
    _booking(db, sample_customer, sample_fundi, status="escrow_funded")
    headers = auth_header_for(app, sample_customer)
    res = client.delete("/api/v1/auth/me", json={"password": "password123"}, headers=headers)
    assert res.status_code == 409
    assert "active jobs" in res.get_json()["error"].lower()


def test_delete_account_refuses_while_wallet_holds_money(app, client, db, sample_fundi):
    sample_fundi.wallet.balance_cents = 5000
    db.session.commit()
    headers = auth_header_for(app, sample_fundi)
    res = client.delete("/api/v1/auth/me", json={"password": "password123"}, headers=headers)
    assert res.status_code == 409
    assert "wallet" in res.get_json()["error"].lower()


def test_delete_account_erases_user_and_finished_history(
    app, client, db, sample_customer, sample_fundi
):
    from server.models.booking import Booking
    from server.models.user import User

    booking = _booking(db, sample_customer, sample_fundi, status="completed")
    booking_id, customer_id, email = booking.id, sample_customer.id, sample_customer.email
    headers = auth_header_for(app, sample_customer)

    res = client.delete("/api/v1/auth/me", json={"password": "password123"}, headers=headers)
    assert res.status_code == 200

    assert db.session.get(User, customer_id) is None
    assert db.session.get(Booking, booking_id) is None
    # The fundi on the other side of that job is untouched.
    assert db.session.get(User, sample_fundi.id) is not None
    # And the email is free again.
    login = client.post(
        "/api/v1/auth/login", json={"email_or_phone": email, "password": "password123"}
    )
    assert login.status_code == 401
