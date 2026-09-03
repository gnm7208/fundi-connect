"""Booking Marshmallow schemas."""

from marshmallow import Schema, fields, validate

from server.schemas.validators import whole_shillings


class BookingCreateSchema(Schema):
    fundi_id = fields.String(required=True)
    service_request_id = fields.String(required=False, allow_none=True)
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    description = fields.String(required=False, allow_none=True)
    agreed_amount_cents = fields.Integer(
        required=True, validate=[validate.Range(min=5000), whole_shillings]
    )  # min KES 50.00
    location_name = fields.String(required=True, validate=validate.Length(min=2, max=150))
    latitude = fields.Float(required=False, allow_none=True)
    longitude = fields.Float(required=False, allow_none=True)
    scheduled_for = fields.DateTime(required=False, allow_none=True)


class BookingStatusUpdateSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            [
                "accepted_unpaid",
                "declined",
                "in_progress",
                "awaiting_confirm",
                "completed",
                "cancelled",
            ]
        ),
    )
