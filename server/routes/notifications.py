"""User notification feed routes."""

from flask import Blueprint, jsonify, request

from server.extensions import db
from server.models.notification import Notification
from server.utils.auth import get_current_authenticated_user, login_required
from server.utils.errors import NotFoundError
from server.utils.pagination import get_pagination_params, paginate_query

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("", methods=["GET"])
@login_required
def list_notifications():
    """List the authenticated user's notifications, newest first."""
    user = get_current_authenticated_user()
    page, per_page = get_pagination_params()

    query = Notification.query.filter_by(user_id=user.id)
    if request.args.get("unread_only", "").lower() in ("true", "1", "yes"):
        query = query.filter_by(is_read=False)

    query = query.order_by(Notification.created_at.desc())
    paginated = paginate_query(query, page, per_page)

    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()

    return (
        jsonify(
            {
                "notifications": [n.to_dict() for n in paginated["items"]],
                "unread_count": unread_count,
                "pagination": paginated["pagination"],
            }
        ),
        200,
    )


@notifications_bp.route("/<string:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id: str):
    """Mark a single notification as read."""
    user = get_current_authenticated_user()
    notification = db.session.get(Notification, notification_id)
    if not notification or notification.user_id != user.id:
        raise NotFoundError("Notification not found")

    notification.is_read = True
    db.session.commit()
    return jsonify({"notification": notification.to_dict()}), 200


@notifications_bp.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    """Mark every unread notification for the user as read."""
    user = get_current_authenticated_user()
    updated = Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All notifications marked as read", "updated": updated}), 200
