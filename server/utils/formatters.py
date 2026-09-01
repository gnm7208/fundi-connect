"""Formatting and normalization utilities for Fundi Connect."""

import re

from server.utils.errors import ValidationError


def normalize_phone_number(phone: str) -> str:
    """Normalize Kenyan phone number to 254XXXXXXXXX format.

    Accepts:
    - 07XXXXXXXX -> 2547XXXXXXXX
    - 01XXXXXXXX -> 2541XXXXXXXX
    - +2547XXXXXXXX -> 2547XXXXXXXX
    - 2547XXXXXXXX -> 2547XXXXXXXX
    """
    if not phone:
        raise ValidationError("Phone number is required")

    cleaned = re.sub(r"[\s\-\(\)\+]", "", phone.strip())

    if cleaned.startswith("0") and len(cleaned) == 10 and cleaned[1] in ("7", "1"):
        return f"254{cleaned[1:]}"
    elif cleaned.startswith("254") and len(cleaned) == 12 and cleaned[3] in ("7", "1"):
        return cleaned
    elif len(cleaned) == 9 and cleaned[0] in ("7", "1"):
        return f"254{cleaned}"
    else:
        raise ValidationError(
            f"Invalid Kenyan phone number format '{phone}'. Use 07XXXXXXXX or 01XXXXXXXX."
        )


def format_kes_currency(cents: int) -> str:
    """Format minor unit cents to human readable KES string."""
    shillings = cents / 100
    return f"KES {shillings:,.2f}"
