"""Tests for customer reviews and dynamic rating calculations."""

from server.models.booking import Booking
from server.tests.conftest import auth_header_for


def test_submit_review_on_completed_booking(app, client, sample_customer, sample_fundi):
    """Customer submits 5-star review after completion, updating fundi rating."""
    cust_headers = auth_header_for(app, sample_customer)

    with app.app_context():
        # Create completed booking
        b = Booking(
            customer_id=sample_customer.id,
            fundi_id=sample_fundi.id,
            title="House Rewiring",
            agreed_amount_cents=500000,
            location_name="Westlands",
            status="completed",
        )
        app.extensions["sqlalchemy"].session.add(b)
        app.extensions["sqlalchemy"].session.commit()
        booking_id = b.id

    res = client.post(
        "/api/v1/reviews",
        json={
            "booking_id": booking_id,
            "rating": 5,
            "review_text": "Excellent craftsmanship, very professional and clean work!",
        },
        headers=cust_headers,
    )
    assert res.status_code == 201
    assert res.get_json()["review"]["rating"] == 5

    # Check reviews list for fundi
    reviews_res = client.get(f"/api/v1/reviews/fundi/{sample_fundi.id}")
    assert reviews_res.status_code == 200
    assert len(reviews_res.get_json()["reviews"]) >= 1


def test_cannot_review_pending_booking(app, client, sample_customer, sample_fundi):
    """Attempting to review a non-completed booking fails with 422."""
    cust_headers = auth_header_for(app, sample_customer)

    with app.app_context():
        b = Booking(
            customer_id=sample_customer.id,
            fundi_id=sample_fundi.id,
            title="Pending Job",
            agreed_amount_cents=100000,
            location_name="CBD",
            status="pending",
        )
        app.extensions["sqlalchemy"].session.add(b)
        app.extensions["sqlalchemy"].session.commit()
        booking_id = b.id

    res = client.post(
        "/api/v1/reviews",
        json={"booking_id": booking_id, "rating": 5},
        headers=cust_headers,
    )
    assert res.status_code == 422
