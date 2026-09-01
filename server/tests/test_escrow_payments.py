"""Tests for M-PESA escrow holding, funding, and auto-release lifecycle."""

from server.models.escrow import EscrowTransaction
from server.models.wallet import Wallet
from server.tests.conftest import auth_header_for


def test_full_escrow_and_payment_flow(app, client, sample_customer, sample_fundi):
    """End-to-End Escrow Lifecycle:

    1. Direct booking created (KES 3,000 agreed).
    2. STK push initiated -> checkout_request_id generated.
    3. M-PESA webhook arrives -> funds held in escrow, booking status=escrow_funded.
    4. Fundi marks job in_progress -> then awaiting_confirm.
    5. Customer confirms completion -> Escrow releases KES 2,700 (90%) to Fundi Wallet!
    """
    cust_headers = auth_header_for(app, sample_customer)
    fundi_headers = auth_header_for(app, sample_fundi)

    # 1. Create Booking (KES 3,000 = 300,000 cents)
    b_res = client.post(
        "/api/v1/bookings",
        json={
            "fundi_id": sample_fundi.id,
            "title": "Kitchen Sink Installation",
            "agreed_amount_cents": 300000,
            "location_name": "Kilimani",
        },
        headers=cust_headers,
    )
    assert b_res.status_code == 201
    booking_id = b_res.get_json()["booking"]["id"]

    # Fundi accepts booking
    client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "accepted_unpaid"},
        headers=fundi_headers,
    )

    # 2. Initiate STK Push
    stk_res = client.post(
        "/api/v1/payments/stk-push",
        json={"booking_id": booking_id, "phone_number": "0711000111"},
        headers=cust_headers,
    )
    assert stk_res.status_code == 200
    checkout_id = stk_res.get_json()["checkout_request_id"]
    assert checkout_id is not None

    # 3. Simulate Successful M-PESA Payment Callback
    cb_res = client.post(
        "/api/v1/payments/simulate-callback",
        json={
            "checkout_request_id": checkout_id,
            "mpesa_receipt_number": "QWE1234567",
        },
    )
    assert cb_res.status_code == 200
    assert cb_res.get_json()["escrow"]["status"] == "held_in_escrow"
    assert cb_res.get_json()["booking_status"] == "escrow_funded"

    # 4. Fundi starts work and finishes
    start_res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "in_progress"},
        headers=fundi_headers,
    )
    assert start_res.status_code == 200

    finish_res = client.patch(
        f"/api/v1/bookings/{booking_id}/status",
        json={"status": "awaiting_confirm"},
        headers=fundi_headers,
    )
    assert finish_res.status_code == 200

    # Check fundi balance before release (starts at KES 5,000 = 500,000 cents in sample_fundi)
    with app.app_context():
        fundi_wallet = Wallet.query.filter_by(user_id=sample_fundi.id).first()
        initial_balance = fundi_wallet.balance_cents

    # 5. Customer confirms completion -> Triggers escrow release
    confirm_res = client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=cust_headers,
    )
    assert confirm_res.status_code == 200
    assert confirm_res.get_json()["booking"]["status"] == "completed"

    # Verify Fundi wallet was credited with KES 2,700 (270,000 cents = 90% of 300,000)
    with app.app_context():
        fundi_wallet = Wallet.query.filter_by(user_id=sample_fundi.id).first()
        assert fundi_wallet.balance_cents == initial_balance + 270000

        escrow = EscrowTransaction.query.filter_by(booking_id=booking_id).first()
        assert escrow.status == "released"
        assert escrow.platform_fee_cents == 30000  # KES 300
        assert escrow.fundi_payout_cents == 270000  # KES 2,700
