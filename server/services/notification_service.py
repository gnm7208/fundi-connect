"""In-app alert and notification dispatcher service."""

from server.extensions import db
from server.models.notification import Notification


class NotificationService:
    """Manages creation and retrieval of user in-app notifications."""

    @classmethod
    def send_notification(
        cls,
        user_id: str,
        title: str,
        message: str,
        notif_type: str = "system",
        data_json: str | None = None,
    ) -> Notification:
        """Create a new notification entry for a user."""
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            data_json=data_json,
        )
        db.session.add(notif)
        db.session.commit()
        return notif
