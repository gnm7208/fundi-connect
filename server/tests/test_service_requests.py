"""Tests for service requests and quoting workflows."""

from server.tests.conftest import auth_header_for


def test_create_service_request(app, client, sample_customer, sample_category):
    """Customer can post an open RFQ/service request."""
    headers = auth_header_for(app, sample_customer)
    payload = {
        "category_id": sample_category.id,
        "title": "Kitchen Sink Pipe Burst",
        "description": "Urgent leak in kitchen, pipe needs replacement today.",
        "location_name": "Kilimani, Argwings Kodhek",
        "budget_min_cents": 150000,
        "budget_max_cents": 300000,
    }
    res = client.post("/api/v1/service-requests", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.get_json()["service_request"]
    assert data["title"] == "Kitchen Sink Pipe Burst"
    assert data["status"] == "open"


def test_submit_quote_and_accept_creates_booking(
    app, client, sample_customer, sample_fundi, sample_category
):
    """Fundi submits a quote and customer accepts it, automatically generating a booking."""
    cust_headers = auth_header_for(app, sample_customer)
    fundi_headers = auth_header_for(app, sample_fundi)

    # 1. Customer creates request
    sr_res = client.post(
        "/api/v1/service-requests",
        json={
            "category_id": sample_category.id,
            "title": "Bathroom Shower Repair",
            "description": "Shower head broken and pipe leaking into wall.",
            "location_name": "Westlands",
        },
        headers=cust_headers,
    )
    sr_id = sr_res.get_json()["service_request"]["id"]

    # 2. Fundi submits quote
    quote_res = client.post(
        f"/api/v1/service-requests/{sr_id}/quotes",
        json={
            "amount_cents": 280000,  # KES 2,800
            "estimated_hours": 2.0,
            "notes": "Includes new stainless steel shower fitting.",
        },
        headers=fundi_headers,
    )
    assert quote_res.status_code == 201
    quote_id = quote_res.get_json()["quote"]["id"]

    # 3. Customer accepts quote
    accept_res = client.post(
        f"/api/v1/service-requests/{sr_id}/quotes/{quote_id}/accept",
        headers=cust_headers,
    )
    assert accept_res.status_code == 201
    booking_data = accept_res.get_json()["booking"]
    assert booking_data["agreed_amount_kes"] == 2800.0
    assert booking_data["status"] == "accepted_unpaid"
    assert booking_data["fundi_id"] == sample_fundi.id
