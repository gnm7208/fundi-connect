"""Tests for admin metrics, verification reviews, and role enforcement."""

from server.models.fundi_profile import FundiProfile
from server.tests.conftest import auth_header_for


def test_admin_metrics_and_role_protection(app, client, sample_admin, sample_customer):
    """Admin can view metrics; non-admin is rejected with 403 Forbidden."""
    admin_headers = auth_header_for(app, sample_admin)
    cust_headers = auth_header_for(app, sample_customer)

    # Admin access
    res = client.get("/api/v1/admin/metrics", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "users" in data
    assert "financials" in data

    # Customer forbidden
    res_forbidden = client.get("/api/v1/admin/metrics", headers=cust_headers)
    assert res_forbidden.status_code == 403


def test_admin_approve_fundi_verification(app, client, sample_admin, sample_fundi):
    """Admin reviews and approves fundi verification status."""
    admin_headers = auth_header_for(app, sample_admin)

    # Set fundi to pending
    with app.app_context():
        p = FundiProfile.query.filter_by(user_id=sample_fundi.id).first()
        p.verification_status = "pending"
        app.extensions["sqlalchemy"].session.commit()

    # Approve
    res = client.patch(
        f"/api/v1/admin/fundis/{sample_fundi.id}/verify",
        json={"status": "verified", "notes": "National ID confirmed via IPRS."},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.get_json()["fundi_profile"]["verification_status"] == "verified"
