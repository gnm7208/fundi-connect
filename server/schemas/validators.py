"""Shared Marshmallow field validators."""

from marshmallow import ValidationError


def whole_shillings(amount_cents: int) -> None:
    """Reject money amounts that are not a whole number of Kenyan shillings.

    M-PESA can only move whole shillings. Allowing sub-shilling amounts in would
    mean the escrow ledger recorded more than Daraja could ever collect or pay out.
    """
    if amount_cents % 100 != 0:
        raise ValidationError(
            "Amount must be a whole number of shillings (a multiple of 100 cents)."
        )
