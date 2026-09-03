"""Wallet and Conversation Marshmallow schemas."""

from marshmallow import Schema, fields, validate

from server.schemas.validators import whole_shillings


class PayoutRequestSchema(Schema):
    amount_cents = fields.Integer(
        required=True, validate=[validate.Range(min=10000), whole_shillings]
    )  # min KES 100 withdrawal
    phone_number = fields.String(required=True)


class ConversationCreateSchema(Schema):
    fundi_id = fields.String(required=True)
    booking_id = fields.String(required=False, allow_none=True)
    initial_message = fields.String(required=False, allow_none=True)


class SendMessageSchema(Schema):
    content = fields.String(required=True, validate=validate.Length(min=1, max=2000))
