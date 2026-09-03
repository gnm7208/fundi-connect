"""Service Request and Quote Marshmallow schemas."""

from marshmallow import Schema, fields, validate

from server.schemas.validators import whole_shillings


class ServiceRequestCreateSchema(Schema):
    category_id = fields.String(required=True)
    title = fields.String(required=True, validate=validate.Length(min=5, max=200))
    description = fields.String(required=True, validate=validate.Length(min=10))
    location_name = fields.String(required=True, validate=validate.Length(min=2, max=150))
    latitude = fields.Float(required=False, allow_none=True)
    longitude = fields.Float(required=False, allow_none=True)
    budget_min_cents = fields.Integer(required=False, validate=validate.Range(min=0))
    budget_max_cents = fields.Integer(required=False, validate=validate.Range(min=0))
    preferred_date = fields.DateTime(required=False, allow_none=True)


class QuoteCreateSchema(Schema):
    amount_cents = fields.Integer(
        required=True, validate=[validate.Range(min=100), whole_shillings]
    )  # min KES 1.00
    estimated_hours = fields.Float(required=False, allow_none=True)
    notes = fields.String(required=False, allow_none=True)
