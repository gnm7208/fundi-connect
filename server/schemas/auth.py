"""Authentication Marshmallow schemas."""

from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    email = fields.Email(required=True)
    phone = fields.String(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))
    full_name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    role = fields.String(
        required=False,
        load_default="customer",
        validate=validate.OneOf(["customer", "fundi", "admin"]),
    )
    # Optional initial fundi profile fields when signing up as fundi
    business_name = fields.String(required=False, allow_none=True)
    location_name = fields.String(required=False, allow_none=True)
    category_id = fields.String(required=False, allow_none=True)
    hourly_rate_cents = fields.Integer(required=False, allow_none=True)


class LoginSchema(Schema):
    email_or_phone = fields.String(required=True)
    password = fields.String(required=True)


class UpdateProfileSchema(Schema):
    full_name = fields.String(required=False, validate=validate.Length(min=2, max=120))
    avatar_url = fields.String(required=False, allow_none=True)
    phone = fields.String(required=False)
