"""Booking workflow and state machine management service."""

from datetime import UTC, datetime

from server.extensions import db
from server.models.booking import Booking
from server.models.notification import Notification
from server.models.user import User
from server.services.escrow_service import EscrowService
from server.utils.errors import ForbiddenError, NotFoundError, StateTransitionError


def utc_now() -> datetime:
    return datetime.now(UTC)


class BookingService:
    """Manages booking agreements and state machine transitions."""

    # Allowed status transitions
    VALID_TRANSITIONS = {
        "pending": ["accepted_unpaid", "declined", "cancelled", "escrow_funded"],
        "accepted_unpaid": ["escrow_funded", "cancelled", "declined"],
        "escrow_funded": ["in_progress", "cancelled", "disputed"],
        "in_progress": ["awaiting_confirm", "disputed"],
        "awaiting_confirm": ["completed", "disputed"],
        "completed": [],
        "declined": [],
        "cancelled": [],
        "disputed": ["completed", "cancelled"],
    }

    @classmethod
    def create_booking(cls, customer: User, data: dict) -> Booking:
        """Create a direct booking agreement."""
        fundi = db.session.get(User, data["fundi_id"])
        if not fundi or not fundi.is_fundi():
            raise NotFoundError("Selected fundi does not exist")

        if fundi.id == customer.id:
            raise ForbiddenError("You cannot book yourself")

        agreed_cents = data["agreed_amount_cents"]
        platform_fee, fundi_payout = EscrowService.calculate_breakdown(agreed_cents)

        booking = Booking(
            customer_id=customer.id,
            fundi_id=fundi.id,
            service_request_id=data.get("service_request_id"),
            title=data["title"],
            description=data.get("description"),
            agreed_amount_cents=agreed_cents,
            platform_fee_cents=platform_fee,
            fundi_amount_cents=fundi_payout,
            location_name=data["location_name"],
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            scheduled_for=data.get("scheduled_for"),
            status="pending",
        )
        db.session.add(booking)
        db.session.flush()

        # Initialize EscrowTransaction
        EscrowService.create_or_get_escrow(booking)

        # Notify fundi
        notification = Notification(
            user_id=fundi.id,
            title="New Booking Request!",
            message=f"{customer.full_name} requested a booking: '{booking.title}' for KES {agreed_cents / 100:,.2f}.",
            type="booking",
        )
        db.session.add(notification)
        db.session.commit()
        return booking

    @classmethod
    def transition_status(
        cls, booking: Booking, new_status: str, actor: User, notes: str | None = None
    ) -> Booking:
        """Advance the booking state machine with RBAC enforcement."""
        current_status = booking.status

        # Validate transition map
        allowed = cls.VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed and not actor.is_admin():
            raise StateTransitionError(
                f"Cannot change booking status from '{current_status}' to '{new_status}'"
            )

        # Role-based permission checks
        if new_status in ("accepted_unpaid", "declined", "in_progress", "awaiting_confirm"):
            if not actor.is_admin() and actor.id != booking.fundi_id:
                raise ForbiddenError("Only the assigned fundi can perform this update")

        if new_status == "completed":
            # Only customer or admin can verify completion
            if not actor.is_admin() and actor.id != booking.customer_id:
                raise ForbiddenError("Only the customer can confirm job completion")
            # Release escrow upon completion
            EscrowService.release_escrow_to_fundi(booking, released_by=actor)
            return booking

        if new_status == "cancelled":
            if not actor.is_admin() and actor.id not in (booking.customer_id, booking.fundi_id):
                raise ForbiddenError("Only the customer, fundi, or admin can cancel this booking")

            if booking.escrow_transaction and booking.escrow_transaction.status == "held_in_escrow":
                EscrowService.refund_escrow_to_customer(
                    booking, reason=notes or "Cancelled by user"
                )
                return booking

        # Apply state updates
        booking.status = new_status
        if new_status == "in_progress" and not booking.started_at:
            booking.started_at = utc_now()
        elif new_status == "cancelled":
            booking.cancelled_at = utc_now()

        # Send alert
        recipient_id = booking.customer_id if actor.id == booking.fundi_id else booking.fundi_id
        notification = Notification(
            user_id=recipient_id,
            title="Booking Status Update",
            message=f"Booking '{booking.title}' status updated to '{new_status}'.",
            type="booking",
        )
        db.session.add(notification)
        db.session.commit()
        return booking
