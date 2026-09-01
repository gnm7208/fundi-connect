"""Tests for health check and general API responsiveness."""


def test_health_check_endpoint(client):
    """Verify /api/health returns 200 OK and online status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "online"
    assert data["service"] == "Fundi Connect API"
    assert data["database"] == "healthy"
