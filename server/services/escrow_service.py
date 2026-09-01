"""Escrow holding and payment lifecycle service."""

from datetime import UTC, datetime

from flask import current_app

from server.extensions import db
from server.models.booking import Booking
from server.models.escrow import EscrowTransaction
from server.models.notification import Notification
from server.models.user import User
from server.models.wallet import Wallet, WalletTransaction
from server.utils.errors import EscrowError, NotFoundError, StateTransitionError


def utc_now() -> datetime:
    return datetime.now(UTC)


class EscrowService:
    """Manages the lifecycle of locked funds in escrow for Fundi Connect."""

    @staticmethod
    def calculate_breakdown(agreed_amount_cents: int) -> tuple[int, int]:
        """Calculate platform commission and fundi payout amount.

        Platform fee is e.g. 10% of agreed amount.
        Fundi payout is 90%.
        Strict integer arithmetic.
        """
        commission_percent = current_app.config.get("PLATFORM_COMMISSION_PERCENT", 10.0)
        # integer math: round to nearest cent
        platform_fee_cents = int(round(agreed_amount_cents * (commission_percent / 100.0)))
        fundi_payout_cents = agreed_amount_cents - platform_fee_cents
        return platform_fee_cents, fundi_payout_cents

    @classmethod
    def create_or_get_escrow(cls, booking: Booking) -> EscrowTransaction:
        """Create or retrieve existing EscrowTransaction record for a booking."""
        if booking.escrow_transaction:
            return booking.escrow_transaction

        platform_fee, fundi_payout = cls.calculate_breakdown(booking.agreed_amount_cents)
        booking.platform_fee_cents = platform_fee
        booking.fundi_amount_cents = fundi_payout

        escrow = EscrowTransaction(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            fundi_id=booking.fundi_id,
            amount_cents=booking.agreed_amount_cents,
            platform_fee_cents=platform_fee,
            fundi_payout_cents=fundi_payout,
            status="pending",
        )
        db.session.add(escrow)
        db.session.commit()
        return escrow

    @classmethod
    def record_stk_push_initiated(
        cls,
        booking: Booking,
        phone_number: str,
        merchant_request_id: str | None,
        checkout_request_id: str,
    ) -> EscrowTransaction:
        """Record checkout request ID on the escrow transaction."""
        escrow = cls.create_or_get_escrow(booking)
        escrow.payment_phone = phone_number
        escrow.merchant_request_id = merchant_request_id
        escrow.checkout_request_id = checkout_request_id
        escrow.status = "pending"
        db.session.commit()
        return escrow

    @classmethod
    def process_successful_payment(
        cls,
        checkout_request_id: str,
        mpesa_receipt_number: str,
        amount_cents: int | None = None,
    ) -> EscrowTransaction:
        """Lock funds into escrow after M-PESA confirmation."""
        escrow = EscrowTransaction.query.filter_by(checkout_request_id=checkout_request_id).first()
        if not escrow:
            raise NotFoundError(
                f"No escrow record found for checkout request '{checkout_request_id}'"
            )

        if escrow.status == "held_in_escrow":
            return escrow  # idempotent

        escrow.status = "held_in_escrow"
        escrow.mpesa_receipt_number = mpesa_receipt_number
        escrow.funded_at = utc_now()

        # Advance booking status to escrow_funded
        booking = escrow.booking
        if booking and booking.status in ("pending", "accepted_unpaid"):
            booking.status = "escrow_funded"

        # Create notifications for both parties
        n_customer = Notification(
            user_id=escrow.customer_id,
            title="Escrow Deposit Confirmed",
            message=f"Your deposit of KES {escrow.amount_cents / 100:,.2f} is safely locked in escrow for '{booking.title if booking else 'Job'}'.",
            type="escrow",
        )
        n_fundi = Notification(
            user_id=escrow.fundi_id,
            title="Funds Locked in Escrow",
            message=f"Customer deposited KES {escrow.amount_cents / 100:,.2f} in escrow for '{booking.title if booking else 'Job'}'. You may now begin work!",
            type="escrow",
        )
        db.session.add_all([n_customer, n_fundi])
        db.session.commit()
        return escrow

    @classmethod
    def release_escrow_to_fundi(
        cls, booking: Booking, released_by: User | None = None
    ) -> EscrowTransaction:
        """Release escrow funds to fundi wallet upon customer confirmation or admin resolution."""
        escrow = booking.escrow_transaction
        if not escrow:
            raise EscrowError("No escrow record exists for this booking")

        if escrow.status not in ("held_in_escrow", "disputed"):
            raise StateTransitionError(
                f"Cannot release escrow in status '{escrow.status}'. Must be 'held_in_escrow' or 'disputed'."
            )

        # 1. Update Escrow status
        escrow.status = "released"
        escrow.released_at = utc_now()

        # 2. Advance Booking status
        booking.status = "completed"
        booking.completed_at = utc_now()

        # 3. Credit Fundi Wallet
        fundi_user = db.session.get(User, booking.fundi_id)
        if not fundi_user.wallet:
            fundi_user.wallet = Wallet(user_id=fundi_user.id, balance_cents=0)
            db.session.add(fundi_user.wallet)
            db.session.flush()

        wallet = fundi_user.wallet
        wallet.balance_cents += escrow.fundi_payout_cents

        # 4. Create Immutable Wallet Transaction
        tx = WalletTransaction(
            wallet_id=wallet.id,
            type="escrow_payout",
            amount_cents=escrow.fundi_payout_cents,
            balance_after_cents=wallet.balance_cents,
            reference=f"BOOKING-{booking.id[:8]}",
            status="completed",
            description=f"Payment for completed job: {booking.title} (Fee: KES {escrow.platform_fee_cents / 100:.2f})",
        )
        db.session.add(tx)

        # 5. Increment Fundi completed jobs count
        if fundi_user.fundi_profile:
            fundi_user.fundi_profile.jobs_completed += 1

        # 6. Notification
        n_fundi = Notification(
            user_id=booking.fundi_id,
            title="Payment Released to Wallet!",
            message=f"KES {escrow.fundi_payout_cents / 100:,.2f} has been credited to your wallet for '{booking.title}'.",
            type="escrow",
        )
        db.session.add(n_fundi)

        db.session.commit()
        return escrow

    @classmethod
    def refund_escrow_to_customer(
        cls, booking: Booking, reason: str = "Job cancelled / refund granted"
    ) -> EscrowTransaction:
        """Refund escrow funds back to customer."""
        escrow = booking.escrow_transaction
        if not escrow:
            raise EscrowError("No escrow record exists for this booking")

        if escrow.status not in ("held_in_escrow", "disputed"):
            raise StateTransitionError(
                f"Cannot refund escrow in status '{escrow.status}'. Must be 'held_in_escrow' or 'disputed'."
            )

        escrow.status = "refunded"
        escrow.refunded_at = utc_now()
        booking.status = "cancelled"
        booking.cancelled_at = utc_now()

        n_customer = Notification(
            user_id=booking.customer_id,
            title="Escrow Refunded",
            message=f"Your deposit of KES {escrow.amount_cents / 100:,.2f} for '{booking.title}' has been refunded ({reason}).",
            type="escrow",
        )
        db.session.add(n_customer)
        db.session.commit()
        return escrow
