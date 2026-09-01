"""Pagination helper for database queries."""

from flask import request


def get_pagination_params(default_limit: int = 20, max_limit: int = 100) -> tuple[int, int]:
    """Extract page and per_page from request query arguments."""
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = min(max_limit, max(1, int(request.args.get("per_page", default_limit))))
    except (ValueError, TypeError):
        per_page = default_limit

    return page, per_page


def paginate_query(query, page: int, per_page: int) -> dict:
    """Execute paginated query and return standardized metadata."""
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if per_page > 0 else 1

    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total,
            "total_pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        },
    }
