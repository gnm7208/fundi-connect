"""Tests for fundi search, geo-filtering, and profile management."""

from server.tests.conftest import auth_header_for


def test_search_fundis_public(client, sample_fundi):
    """Verify public can search and discover fundis."""
    res = client.get("/api/v1/fundis/search")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] >= 1
    assert data["fundis"][0]["business_name"] == "Mwangi Fast Fixes"


def test_search_fundis_geo_radius(client, sample_fundi):
    """Verify distance calculation from Nairobi CBD to Kilimani (~3.8 km)."""
    # Nairobi CBD coordinates: -1.286389, 36.817223
    res = client.get("/api/v1/fundis/search?lat=-1.286389&lng=36.817223&radius_km=10")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] >= 1
    assert data["fundis"][0]["distance_km"] is not None
    assert data["fundis"][0]["distance_km"] < 10.0


def test_get_fundi_detail(client, sample_fundi):
    """Get single fundi public details."""
    res = client.get(f"/api/v1/fundis/{sample_fundi.id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["fundi"]["full_name"] == sample_fundi.full_name
    assert len(data["fundi"]["skills"]) >= 1


def test_update_fundi_profile(app, client, sample_fundi):
    """Fundi can update their pricing and location."""
    headers = auth_header_for(app, sample_fundi)
    update_data = {
        "business_name": "Mwangi Premium Plumbing",
        "hourly_rate_cents": 220000,  # KES 2,200/hr
        "service_radius_km": 30.0,
    }
    res = client.patch("/api/v1/fundis/profile", json=update_data, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["fundi_profile"]["business_name"] == "Mwangi Premium Plumbing"
    assert res.get_json()["fundi_profile"]["hourly_rate_kes"] == 2200.0


def test_submit_id_verification(app, client, sample_fundi):
    """Fundi submits ID documents for badge review."""
    headers = auth_header_for(app, sample_fundi)
    id_data = {
        "id_number": "12345678",
        "id_document_url": "https://example.com/docs/my_national_id.pdf",
    }
    res = client.post("/api/v1/fundis/verify-id", json=id_data, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["verification_status"] == "pending"
