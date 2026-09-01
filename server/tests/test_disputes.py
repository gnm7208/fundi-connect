"""Tests for dispute filing and administrative resolution."""

from server.models.booking import Booking
from server.models.escrow import EscrowTransaction
from server.tests.conftest import auth_header_for


def test_file_dispute_and_admin_refund(app, client, sample_customer, sample_fundi, sample_admin):
    """Customer files dispute on an escrowed booking, admin resolves with refund."""
    cust_headers = auth_header_for(app, sample_customer)
    admin_headers = auth_header_for(app, sample_admin)

    with app.app_context():
        b = Booking(
            customer_id=sample_customer.id,
            fundi_id=sample_fundi.id,
            title="Roof Tile Replacement",
            agreed_amount_cents=400000,
            location_name="Runda",
            status="in_progress",
        )
        app.extensions["sqlalchemy"].session.add(b)
        app.extensions["sqlalchemy"].session.flush()

        escrow = EscrowTransaction(
            booking_id=b.id,
            customer_id=sample_customer.id,
            fundi_id=sample_fundi.id,
            amount_cents=400000,
            platform_fee_cents=40000,
            fundi_payout_cents=360000,
            status="held_in_escrow",
        )
        app.extensions["sqlalchemy"].session.add(escrow)
        app.extensions["sqlalchemy"].session.commit()
        booking_id = b.id

    # 1. Customer files dispute
    disp_res = client.post(
        "/api/v1/disputes",
        json={
            "booking_id": booking_id,
            "reason": "Fundi did not show up and stopped picking calls",
            "customer_statement": "Waited 3 days, roof is still leaking.",
        },
        headers=cust_headers,
    )
    assert disp_res.status_code == 201
    dispute_id = disp_res.get_json()["dispute"]["id"]

    # 2. Admin reviews and resolves with customer refund
    resolve_res = client.post(
        f"/api/v1/admin/disputes/{dispute_id}/resolve",
        json={
            "action": "refund_customer",
            "resolution": "Customer confirmed no-show with evidence. Refunding full escrow deposit.",
        },
        headers=admin_headers,
    )
    assert resolve_res.status_code == 200
    assert resolve_res.get_json()["dispute"]["status"] == "resolved_refund"

    with app.app_context():
        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        assert escrow.status == "refunded"
