"""Dispute Marshmallow schemas."""

from marshmallow import Schema, fields, validate


class DisputeCreateSchema(Schema):
    booking_id = fields.String(required=True)
    reason = fields.String(required=True, validate=validate.Length(min=5, max=200))
    customer_statement = fields.String(required=True, validate=validate.Length(min=10))


class DisputeResponseSchema(Schema):
    fundi_statement = fields.String(required=True, validate=validate.Length(min=10))


class DisputeResolveSchema(Schema):
    resolution = fields.String(required=True, validate=validate.Length(min=5))
    action = fields.String(
        required=True,
        validate=validate.OneOf(["refund_customer", "payout_fundi"]),
    )
