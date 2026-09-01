"""Category and trade catalogue routes."""

from flask import Blueprint, jsonify, request

from server.extensions import db
from server.models.category import Category
from server.schemas.category import CategoryCreateSchema, CategoryUpdateSchema
from server.utils.auth import admin_required
from server.utils.errors import ConflictError, NotFoundError, ValidationError

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("", methods=["GET"])
def get_categories():
    """List all active service categories."""
    categories = Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()
    return jsonify({"categories": [cat.to_dict() for cat in categories]}), 200


@categories_bp.route("/<string:cat_id_or_slug>", methods=["GET"])
def get_category_detail(cat_id_or_slug: str):
    """Get single category details."""
    cat = Category.query.filter(
        (Category.id == cat_id_or_slug) | (Category.slug == cat_id_or_slug)
    ).first()
    if not cat:
        raise NotFoundError("Category not found")
    return jsonify({"category": cat.to_dict()}), 200


@categories_bp.route("", methods=["POST"])
@admin_required
def create_category():
    """Create a new service category (Admin only)."""
    schema = CategoryCreateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    slug = data.get("slug") or data["name"].lower().replace(" ", "-")

    if Category.query.filter_by(name=data["name"]).first():
        raise ConflictError("A category with this name already exists")

    cat = Category(
        name=data["name"],
        slug=slug,
        description=data.get("description"),
        icon=data.get("icon"),
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify({"message": "Category created", "category": cat.to_dict()}), 201


@categories_bp.route("/<string:category_id>", methods=["PATCH"])
@admin_required
def update_category(category_id: str):
    """Update category properties (Admin only)."""
    cat = db.session.get(Category, category_id)
    if not cat:
        raise NotFoundError("Category not found")

    schema = CategoryUpdateSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    for key, value in data.items():
        if hasattr(cat, key):
            setattr(cat, key, value)

    db.session.commit()
    return jsonify({"message": "Category updated", "category": cat.to_dict()}), 200
