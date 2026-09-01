"""In-app direct messaging routes between customers and fundis."""

from datetime import UTC, datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from server.extensions import db
from server.models.conversation import Conversation, Message
from server.models.notification import Notification
from server.models.user import User
from server.schemas.wallet import ConversationCreateSchema, SendMessageSchema
from server.utils.auth import get_current_authenticated_user, login_required
from server.utils.errors import ForbiddenError, NotFoundError, ValidationError

conversations_bp = Blueprint("conversations", __name__)


def utc_now():
    return datetime.now(UTC)


@conversations_bp.route("", methods=["GET"])
@login_required
def list_conversations():
    """List all active chat conversations for the logged in user."""
    user = get_current_authenticated_user()
    threads = (
        Conversation.query.filter(
            or_(Conversation.customer_id == user.id, Conversation.fundi_id == user.id)
        )
        .order_by(Conversation.last_message_at.desc())
        .all()
    )

    return jsonify({"conversations": [t.to_dict() for t in threads]}), 200


@conversations_bp.route("", methods=["POST"])
@login_required
def create_or_get_conversation():
    """Start or retrieve conversation thread with a fundi."""
    user = get_current_authenticated_user()
    schema = ConversationCreateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    fundi = db.session.get(User, data["fundi_id"])
    if not fundi or not fundi.is_fundi():
        raise NotFoundError("Fundi not found")

    thread = Conversation.query.filter_by(
        customer_id=user.id, fundi_id=fundi.id, booking_id=data.get("booking_id")
    ).first()

    if not thread:
        thread = Conversation(
            customer_id=user.id,
            fundi_id=fundi.id,
            booking_id=data.get("booking_id"),
        )
        db.session.add(thread)
        db.session.flush()

    if data.get("initial_message"):
        msg = Message(
            conversation_id=thread.id,
            sender_id=user.id,
            content=data["initial_message"],
        )
        thread.last_message_at = utc_now()
        db.session.add(msg)

    db.session.commit()
    return jsonify({"conversation": thread.to_dict(include_messages=True)}), 200


@conversations_bp.route("/<string:conversation_id>", methods=["GET"])
@login_required
def get_conversation_messages(conversation_id: str):
    """Get all messages in a conversation."""
    user = get_current_authenticated_user()
    thread = db.session.get(Conversation, conversation_id)
    if not thread:
        raise NotFoundError("Conversation not found")

    if user.id not in (thread.customer_id, thread.fundi_id) and not user.is_admin():
        raise ForbiddenError("Unauthorized access to this conversation")

    # Mark unread messages as read
    for msg in thread.messages:
        if msg.sender_id != user.id and not msg.read_at:
            msg.read_at = utc_now()
    db.session.commit()

    return jsonify({"conversation": thread.to_dict(include_messages=True)}), 200


@conversations_bp.route("/<string:conversation_id>/messages", methods=["POST"])
@login_required
def send_message(conversation_id: str):
    """Send a message within a conversation."""
    user = get_current_authenticated_user()
    thread = db.session.get(Conversation, conversation_id)
    if not thread:
        raise NotFoundError("Conversation not found")

    if user.id not in (thread.customer_id, thread.fundi_id) and not user.is_admin():
        raise ForbiddenError("Unauthorized")

    schema = SendMessageSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    msg = Message(
        conversation_id=thread.id,
        sender_id=user.id,
        content=data["content"],
    )
    thread.last_message_at = utc_now()
    db.session.add(msg)

    # Notify recipient
    recipient_id = thread.fundi_id if user.id == thread.customer_id else thread.customer_id
    n = Notification(
        user_id=recipient_id,
        title="New Message",
        message=f"{user.full_name}: {msg.content[:50]}...",
        type="message",
    )
    db.session.add(n)
    db.session.commit()

    return jsonify({"message": "Message sent", "data": msg.to_dict()}), 201
