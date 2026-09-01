"""Tests for booking creation and state machine transitions."""

from server.tests.conftest import auth_header_for


def test_create_direct_booking(app, client, sample_customer, sample_fundi):
    """Customer can create a direct booking for a fundi."""
    headers = auth_header_for(app, sample_customer)
    payload = {
        "fundi_id": sample_fundi.id,
        "title": "Fix Washing Machine Drainage",
        "description": "Drain pump is clogged and water doesn't exit.",
        "agreed_amount_cents": 250000,  # KES 2,500
        "location_name": "Kilimani, Wood Avenue",
    }
    res = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert res.status_code == 201
    booking = res.get_json()["booking"]
    assert booking["title"] == "Fix Washing Machine Drainage"
    assert booking["agreed_amount_kes"] == 2500.0
    assert booking["platform_fee_kes"] == 250.0  # 10%
    assert booking["fundi_amount_kes"] == 2250.0  # 90%
    assert booking["status"] == "pending"


def test_fundi_accepts_booking(app, client, sample_customer, sample_fundi):
    """Fundi transitions booking from pending to accepted_unpaid."""
    cust_headers = auth_header_for(app, sample_customer)
    fundi_headers = auth_header_for(app, sample_fundi)

    # 1. Customer creates booking
    create_res = client.post(
        "/api/v1/bookings",
        json={
            "fundi_id": sample_fundi.id,
            "title": "Install Water Heater",
            "agreed_amount_cents": 400000,  # KES 4,000
            "location_name": "Lavington",
        },
        headers=cust_headers,
    )
    b_id = create_res.get_json()["booking"]["id"]

    # 2. Fundi accepts
    accept_res = client.patch(
        f"/api/v1/bookings/{b_id}/status",
        json={"status": "accepted_unpaid"},
        headers=fundi_headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.get_json()["booking"]["status"] == "accepted_unpaid"


def test_invalid_status_transition_rejected(app, client, sample_customer, sample_fundi):
    """Attempting invalid status transition (e.g. pending -> completed) is rejected."""
    cust_headers = auth_header_for(app, sample_customer)

    create_res = client.post(
        "/api/v1/bookings",
        json={
            "fundi_id": sample_fundi.id,
            "title": "Quick Fix",
            "agreed_amount_cents": 100000,
            "location_name": "South C",
        },
        headers=cust_headers,
    )
    b_id = create_res.get_json()["booking"]["id"]

    # Try skipping escrow funding
    bad_res = client.patch(
        f"/api/v1/bookings/{b_id}/status",
        json={"status": "in_progress"},
        headers=cust_headers,
    )
    assert bad_res.status_code == 400
    assert "Cannot change booking status" in bad_res.get_json()["error"]
