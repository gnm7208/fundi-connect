"""Dispute model for Fundi Connect."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.extensions import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Dispute(db.Model):
    """Dispute filed on a booking when service delivery or terms are contested."""

    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    booking_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    initiated_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    fundi_statement: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Resolution details
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Status: open, under_review, resolved_refund (customer gets money), resolved_payout (fundi gets money)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking = relationship("Booking", back_populates="dispute")
    initiator = relationship("User", foreign_keys=[initiated_by_id])
    resolver = relationship("User", foreign_keys=[resolved_by_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "initiated_by_id": self.initiated_by_id,
            "initiator_name": self.initiator.full_name if self.initiator else None,
            "reason": self.reason,
            "customer_statement": self.customer_statement,
            "fundi_statement": self.fundi_statement,
            "resolution": self.resolution,
            "resolved_by_id": self.resolved_by_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
