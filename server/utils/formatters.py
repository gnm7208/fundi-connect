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


def to_whole_shillings(amount_cents: int) -> int:
    """Convert minor units to the whole shillings M-PESA transacts in.

    Daraja only moves whole shillings, so a remainder here would mean charging the
    customer less than the escrow record claims was collected. Refuse instead of
    silently truncating; amounts are constrained to whole shillings at the API boundary.
    """
    if amount_cents % 100 != 0:
        raise ValidationError(
            f"M-PESA transacts in whole shillings, but the amount is {amount_cents} cents."
        )
    return amount_cents // 100


def format_kes_currency(cents: int) -> str:
    """Format minor unit cents to human readable KES string."""
    shillings = cents / 100
    return f"KES {shillings:,.2f}"
