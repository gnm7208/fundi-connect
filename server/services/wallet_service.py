"""Fundi wallet ledger and payout withdrawal service."""

from server.extensions import db
from server.models.user import User
from server.models.wallet import Wallet, WalletTransaction
from server.services.daraja_service import DarajaService
from server.utils.errors import EscrowError, ForbiddenError, ValidationError


class WalletService:
    """Manages fundi wallet balances, ledger entries, and M-PESA payouts."""

    @classmethod
    def get_user_wallet(cls, user: User) -> Wallet:
        """Get or initialize user's wallet."""
        wallet = user.wallet
        if not wallet:
            wallet = Wallet(user_id=user.id, balance_cents=0)
            db.session.add(wallet)
            db.session.commit()
        return wallet

    @classmethod
    def request_payout(cls, user: User, amount_cents: int, phone_number: str) -> dict:
        """Request withdrawal of earned funds via M-PESA B2C payout."""
        if not user.is_fundi() and not user.is_admin():
            raise ForbiddenError("Only service providers can withdraw wallet earnings")

        wallet = cls.get_user_wallet(user)
        if wallet.is_frozen:
            raise ForbiddenError("Wallet is currently frozen. Please contact support.")

        if amount_cents > wallet.balance_cents:
            raise ValidationError(
                f"Insufficient wallet balance. Available: KES {wallet.balance_cents / 100:,.2f}"
            )

        # 1. Debit Wallet
        wallet.balance_cents -= amount_cents

        # 2. Record Transaction
        tx = WalletTransaction(
            wallet_id=wallet.id,
            type="withdrawal",
            amount_cents=-amount_cents,
            balance_after_cents=wallet.balance_cents,
            status="completed",
            description=f"M-PESA Payout to {phone_number}",
        )
        db.session.add(tx)
        db.session.flush()

        # 3. Trigger Daraja B2C Payout
        daraja = DarajaService()
        payout_result = daraja.initiate_b2c_payout(
            phone_number=phone_number,
            amount_cents=amount_cents,
            transaction_id=tx.id,
        )

        if not payout_result.get("success"):
            # Rollback wallet debit if external transfer fails hard
            wallet.balance_cents += amount_cents
            tx.status = "failed"
            db.session.commit()
            raise EscrowError(
                f"M-PESA payout failed: {payout_result.get('ResponseDescription', 'Service error')}"
            )

        tx.reference = payout_result.get("ReceiptNumber") or payout_result.get("ConversationID")
        db.session.commit()

        return {
            "success": True,
            "transaction": tx.to_dict(),
            "payout_details": payout_result,
            "new_balance_kes": wallet.balance_cents / 100,
        }
