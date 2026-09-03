"""Tests for M-PESA escrow holding, funding, and auto-release lifecycle."""

import pytest

from server.models.escrow import EscrowTransaction
from server.models.wallet import Wallet
from server.services.escrow_service import EscrowService
from server.tests.conftest import auth_header_for


def fund_booking(client, app, customer, fundi, amount_cents: int) -> tuple[str, str]:
    """Create a booking and take it up to a pending STK push. Returns (booking_id, checkout_id)."""
    cust_headers = auth_header_for(app, customer)
    b_res = client.post(
        "/api/v1/bookings",
        json={
            "fundi_id": fundi.id,
            "title": "Kitchen Sink Installation",
            "agreed_amount_cents": amount_cents,
            "location_name": "Kilimani",
        },
        headers=cust_headers,
    )
    assert b_res.status_code == 201
    booking_id = b_res.get_json()["booking"]["id"]

    stk_res = client.post(
        "/api/v1/payments/stk-push",
        json={"booking_id": booking_id, "phone_number": "0711000111"},
        headers=cust_headers,
    )
    assert stk_res.status_code == 200
    return booking_id, stk_res.get_json()["checkout_request_id"]


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
        headers=cust_headers,
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


def test_simulate_callback_rejects_anonymous_caller(app, client, sample_customer, sample_fundi):
    """The demo funding endpoint must not let a stranger mark escrow as paid."""
    _, checkout_id = fund_booking(client, app, sample_customer, sample_fundi, 300000)

    res = client.post(
        "/api/v1/payments/simulate-callback",
        json={"checkout_request_id": checkout_id},
    )
    assert res.status_code == 401

    with app.app_context():
        escrow = EscrowTransaction.query.filter_by(checkout_request_id=checkout_id).first()
        assert escrow.status == "pending"


def test_simulate_callback_rejects_other_customer(app, client, sample_customer, sample_fundi, db):
    """Only the paying customer can confirm their own transaction."""
    from server.models.user import User

    intruder = User(
        email="intruder@example.com",
        phone="254733000333",
        role="customer",
        full_name="Not Your Customer",
    )
    intruder.set_password("password123")
    db.session.add(intruder)
    db.session.commit()

    _, checkout_id = fund_booking(client, app, sample_customer, sample_fundi, 300000)

    res = client.post(
        "/api/v1/payments/simulate-callback",
        json={"checkout_request_id": checkout_id},
        headers=auth_header_for(app, intruder),
    )
    assert res.status_code == 403


def test_underpaid_callback_does_not_fund_escrow(app, client, sample_customer, sample_fundi):
    """A short M-PESA payment must leave the job unfunded rather than release later."""
    _, checkout_id = fund_booking(client, app, sample_customer, sample_fundi, 300000)

    callback = {
        "Body": {
            "stkCallback": {
                "CheckoutRequestID": checkout_id,
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 100},  # KES 100 against a KES 3,000 job
                        {"Name": "MpesaReceiptNumber", "Value": "QWE1234567"},
                    ]
                },
            }
        }
    }
    res = client.post("/api/v1/payments/daraja/callback", json=callback)
    assert res.status_code == 200  # acknowledged so Safaricom stops retrying

    with app.app_context():
        escrow = EscrowTransaction.query.filter_by(checkout_request_id=checkout_id).first()
        assert escrow.status == "failed"
        assert escrow.booking.status != "escrow_funded"


def test_booking_rejects_sub_shilling_amount(app, client, sample_customer, sample_fundi):
    """M-PESA cannot move fractional shillings, so the ledger must not record them."""
    res = client.post(
        "/api/v1/bookings",
        json={
            "fundi_id": sample_fundi.id,
            "title": "Leaky tap repair",
            "agreed_amount_cents": 150050,  # KES 1,500.50
            "location_name": "Kilimani",
        },
        headers=auth_header_for(app, sample_customer),
    )
    assert res.status_code == 422


@pytest.mark.parametrize(
    ("amount_cents", "expected_fee"),
    [
        (300000, 30000),
        (100, 10),
        (150, 15),
        (12345, 1235),  # rounds half up, never loses a cent
    ],
)
def test_commission_breakdown_is_exact_integer_split(app, amount_cents, expected_fee):
    """Fee plus payout must always reconstruct the exact amount the customer escrowed."""
    with app.app_context():
        fee, payout = EscrowService.calculate_breakdown(amount_cents)
        assert fee == expected_fee
        assert fee + payout == amount_cents
        assert isinstance(fee, int) and isinstance(payout, int)
