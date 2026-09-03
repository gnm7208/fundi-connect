"""Tests for the notification feed and session refresh."""

from flask_jwt_extended import create_refresh_token

from server.models.notification import Notification
from server.tests.conftest import auth_header_for


def test_notification_feed_is_scoped_to_the_user(app, client, db, sample_customer, sample_fundi):
    db.session.add_all(
        [
            Notification(user_id=sample_customer.id, title="Yours", message="For the customer"),
            Notification(user_id=sample_fundi.id, title="Theirs", message="For the fundi"),
        ]
    )
    db.session.commit()

    res = client.get("/api/v1/notifications", headers=auth_header_for(app, sample_customer))
    assert res.status_code == 200

    body = res.get_json()
    assert [n["title"] for n in body["notifications"]] == ["Yours"]
    assert body["unread_count"] == 1


def test_mark_all_notifications_read(app, client, db, sample_customer):
    db.session.add_all(
        [
            Notification(user_id=sample_customer.id, title="One", message="First"),
            Notification(user_id=sample_customer.id, title="Two", message="Second"),
        ]
    )
    db.session.commit()

    headers = auth_header_for(app, sample_customer)
    assert client.post("/api/v1/notifications/read-all", headers=headers).status_code == 200

    res = client.get("/api/v1/notifications?unread_only=true", headers=headers)
    assert res.get_json()["notifications"] == []


def test_refresh_token_issues_a_new_access_token(app, client, sample_customer):
    with app.app_context():
        refresh_token = create_refresh_token(identity=sample_customer.id)

    res = client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert res.status_code == 200

    body = res.get_json()
    assert body["access_token"]
    assert body["user"]["id"] == sample_customer.id


def test_refresh_rejects_an_access_token(app, client, sample_customer):
    """An access token must not be usable to mint further access tokens."""
    res = client.post("/api/v1/auth/refresh", headers=auth_header_for(app, sample_customer))
    assert res.status_code == 422
