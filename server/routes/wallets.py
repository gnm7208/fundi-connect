"""Fundi wallet ledger and payout withdrawal routes."""

from flask import Blueprint, jsonify, request

from server.extensions import limiter
from server.models.wallet import WalletTransaction
from server.schemas.wallet import PayoutRequestSchema
from server.services.wallet_service import WalletService
from server.utils.auth import fundi_required, get_current_authenticated_user
from server.utils.errors import ValidationError
from server.utils.pagination import get_pagination_params, paginate_query

wallets_bp = Blueprint("wallets", __name__)


@wallets_bp.route("/me", methods=["GET"])
@fundi_required
def get_my_wallet():
    """Retrieve authenticated fundi's wallet balance and summary."""
    user = get_current_authenticated_user()
    wallet = WalletService.get_user_wallet(user)
    return jsonify({"wallet": wallet.to_dict()}), 200


@wallets_bp.route("/me/transactions", methods=["GET"])
@fundi_required
def get_my_wallet_transactions():
    """Retrieve paginated wallet transactions ledger."""
    user = get_current_authenticated_user()
    wallet = WalletService.get_user_wallet(user)
    page, per_page = get_pagination_params()

    query = WalletTransaction.query.filter_by(wallet_id=wallet.id).order_by(
        WalletTransaction.created_at.desc()
    )
    paginated = paginate_query(query, page, per_page)

    return (
        jsonify(
            {
                "transactions": [tx.to_dict() for tx in paginated["items"]],
                "balance_kes": wallet.balance_cents / 100,
                "pagination": paginated["pagination"],
            }
        ),
        200,
    )


@wallets_bp.route("/payout-request", methods=["POST"])
@fundi_required
@limiter.limit("5 per minute")
def request_payout():
    """Request M-PESA B2C withdrawal of earned wallet balance."""
    user = get_current_authenticated_user()
    schema = PayoutRequestSchema()
    errors = schema.validate(request.get_json() or {})
    if errors:
        raise ValidationError("Validation failed", payload={"fields": errors})

    data = schema.load(request.get_json() or {})
    result = WalletService.request_payout(
        user=user,
        amount_cents=data["amount_cents"],
        phone_number=data["phone_number"],
    )

    return (
        jsonify(
            {
                "message": f"Withdrawal of KES {data['amount_cents'] / 100:,.2f} processed successfully to {data['phone_number']}.",
                "payout": result,
            }
        ),
        200,
    )
