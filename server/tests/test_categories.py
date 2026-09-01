"""Tests for categories catalogue routes."""

from server.tests.conftest import auth_header_for


def test_list_categories(client, sample_category):
    """Public can list all active categories."""
    res = client.get("/api/v1/categories")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["categories"]) >= 1
    assert data["categories"][0]["slug"] == sample_category.slug


def test_get_category_by_slug_and_id(client, sample_category):
    """Retrieve single category by slug or id."""
    # By slug
    res_slug = client.get(f"/api/v1/categories/{sample_category.slug}")
    assert res_slug.status_code == 200
    assert res_slug.get_json()["category"]["name"] == sample_category.name

    # By id
    res_id = client.get(f"/api/v1/categories/{sample_category.id}")
    assert res_id.status_code == 200
    assert res_id.get_json()["category"]["slug"] == sample_category.slug


def test_create_category_admin_only(app, client, sample_admin, sample_customer):
    """Admin can create new categories; customer is forbidden."""
    admin_headers = auth_header_for(app, sample_admin)
    cust_headers = auth_header_for(app, sample_customer)

    # Customer attempt
    res_forbidden = client.post(
        "/api/v1/categories",
        json={"name": "Carpentry", "description": "Woodwork and joinery"},
        headers=cust_headers,
    )
    assert res_forbidden.status_code == 403

    # Admin attempt
    res_admin = client.post(
        "/api/v1/categories",
        json={"name": "Carpentry", "description": "Woodwork and joinery", "icon": "Hammer"},
        headers=admin_headers,
    )
    assert res_admin.status_code == 201
    assert res_admin.get_json()["category"]["name"] == "Carpentry"


def test_update_category_admin(app, client, sample_admin, sample_category):
    """Admin can update category attributes."""
    admin_headers = auth_header_for(app, sample_admin)
    res = client.patch(
        f"/api/v1/categories/{sample_category.id}",
        json={"description": "Updated plumbing and drainage services", "icon": "WrenchAlt"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.get_json()["category"]["icon"] == "WrenchAlt"
