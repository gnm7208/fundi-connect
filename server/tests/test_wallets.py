"""Tests for fundi wallet ledger and M-PESA payout withdrawals."""

from server.tests.conftest import auth_header_for


def test_get_wallet_balance_and_transactions(app, client, sample_fundi):
    """Fundi can inspect their wallet balance and transaction ledger."""
    headers = auth_header_for(app, sample_fundi)
    res = client.get("/api/v1/wallets/me", headers=headers)
    assert res.status_code == 200
    data = res.get_json()["wallet"]
    assert data["balance_kes"] == 5000.0


def test_request_payout_withdrawal_success(app, client, sample_fundi):
    """Fundi requests withdrawal of KES 2,000 to M-PESA."""
    headers = auth_header_for(app, sample_fundi)
    payout_data = {
        "amount_cents": 200000,  # KES 2,000
        "phone_number": "0722000222",
    }
    res = client.post("/api/v1/wallets/payout-request", json=payout_data, headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["payout"]["new_balance_kes"] == 3000.0  # 5,000 - 2,000


def test_request_payout_insufficient_funds(app, client, sample_fundi):
    """Overdrawing wallet balance returns 422 validation error."""
    headers = auth_header_for(app, sample_fundi)
    payout_data = {
        "amount_cents": 1000000,  # KES 10,000 (balance is 5,000)
        "phone_number": "0722000222",
    }
    res = client.post("/api/v1/wallets/payout-request", json=payout_data, headers=headers)
    assert res.status_code == 422
    assert "Insufficient wallet balance" in res.get_json()["error"]
