"""Fundi profile and search Marshmallow schemas."""

from marshmallow import Schema, fields, validate


class FundiProfileUpdateSchema(Schema):
    business_name = fields.String(required=False, allow_none=True)
    bio = fields.String(required=False, allow_none=True)
    experience_years = fields.Integer(required=False, validate=validate.Range(min=0, max=60))
    location_name = fields.String(required=False, allow_none=True)
    latitude = fields.Float(required=False, allow_none=True)
    longitude = fields.Float(required=False, allow_none=True)
    service_radius_km = fields.Float(required=False, validate=validate.Range(min=1, max=100))
    hourly_rate_cents = fields.Integer(required=False, validate=validate.Range(min=0))
    is_available = fields.Boolean(required=False)


class FundiVerificationSchema(Schema):
    id_number = fields.String(required=True, validate=validate.Length(min=5, max=50))
    id_document_url = fields.String(required=True, validate=validate.Length(min=5, max=500))


class AddSkillSchema(Schema):
    category_id = fields.String(required=True)
    skill_name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    experience_years = fields.Integer(required=False, load_default=1)
    certification_url = fields.String(required=False, allow_none=True)


class FundiSearchQuerySchema(Schema):
    q = fields.String(required=False)
    category = fields.String(required=False)  # category id or slug
    lat = fields.Float(required=False)
    lng = fields.Float(required=False)
    radius_km = fields.Float(required=False, load_default=25.0)
    verified_only = fields.Boolean(required=False, load_default=False)
    min_rating = fields.Float(required=False)
    sort = fields.String(
        required=False,
        load_default="rating",
        validate=validate.OneOf(["rating", "distance", "jobs", "rate_asc", "rate_desc"]),
    )
    # Declared so the schema accepts them; the values are read by get_pagination_params.
    page = fields.Integer(required=False, validate=validate.Range(min=1))
    per_page = fields.Integer(required=False, validate=validate.Range(min=1, max=100))
