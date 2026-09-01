"""EscrowTransaction model for Fundi Connect."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.extensions import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class EscrowTransaction(db.Model):
    """Escrow holding ledger and M-PESA Daraja tracking record for a booking."""

    __tablename__ = "escrow_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    booking_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    fundi_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Money (Minor units KES cents)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_fee_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    fundi_payout_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    # Escrow Status
    # pending -> held_in_escrow -> released (to fundi) / refunded (to customer) / disputed
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)

    # Daraja M-PESA identifiers
    merchant_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    checkout_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    mpesa_receipt_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    payment_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Timestamps
    funded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    booking = relationship("Booking", back_populates="escrow_transaction")
    customer = relationship("User", foreign_keys=[customer_id])
    fundi = relationship("User", foreign_keys=[fundi_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "customer_id": self.customer_id,
            "fundi_id": self.fundi_id,
            "amount_cents": self.amount_cents,
            "amount_kes": self.amount_cents / 100,
            "platform_fee_cents": self.platform_fee_cents,
            "platform_fee_kes": self.platform_fee_cents / 100,
            "fundi_payout_cents": self.fundi_payout_cents,
            "fundi_payout_kes": self.fundi_payout_cents / 100,
            "status": self.status,
            "mpesa_receipt_number": self.mpesa_receipt_number,
            "payment_phone": self.payment_phone,
            "funded_at": self.funded_at.isoformat() if self.funded_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "refunded_at": self.refunded_at.isoformat() if self.refunded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
