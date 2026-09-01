"""Review Marshmallow schemas."""

from marshmallow import Schema, fields, validate


class ReviewCreateSchema(Schema):
    booking_id = fields.String(required=True)
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    review_text = fields.String(required=False, allow_none=True)
