"""Category Marshmallow schemas."""

from marshmallow import Schema, fields, validate


class CategoryCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    slug = fields.String(required=False, validate=validate.Length(min=2, max=100))
    description = fields.String(required=False, allow_none=True)
    icon = fields.String(required=False, allow_none=True)


class CategoryUpdateSchema(Schema):
    name = fields.String(required=False, validate=validate.Length(min=2, max=100))
    description = fields.String(required=False, allow_none=True)
    icon = fields.String(required=False, allow_none=True)
    is_active = fields.Boolean(required=False)
