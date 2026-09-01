"""Booking model for Fundi Connect."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.extensions import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Booking(db.Model):
    """Job booking agreement between a customer and a fundi."""

    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fundi_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_request_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("service_requests.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Financials (in minor units KES cents)
    agreed_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    fundi_amount_cents: Mapped[int] = mapped_column(Integer, default=0)

    # Status Workflow
    # pending -> accepted_unpaid -> escrow_funded -> in_progress -> awaiting_confirm -> completed
    # Side states: declined, cancelled, disputed
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)

    # Location & Schedule
    location_name: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    customer = relationship("User", foreign_keys=[customer_id], back_populates="customer_bookings")
    fundi = relationship("User", foreign_keys=[fundi_id], back_populates="fundi_bookings")
    service_request = relationship("ServiceRequest", back_populates="bookings")
    escrow_transaction = relationship(
        "EscrowTransaction", back_populates="booking", uselist=False, cascade="all, delete-orphan"
    )
    review = relationship(
        "Review", back_populates="booking", uselist=False, cascade="all, delete-orphan"
    )
    dispute = relationship(
        "Dispute", back_populates="booking", uselist=False, cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.full_name if self.customer else None,
            "customer_phone": self.customer.phone if self.customer else None,
            "fundi_id": self.fundi_id,
            "fundi_name": self.fundi.full_name if self.fundi else None,
            "fundi_phone": self.fundi.phone if self.fundi else None,
            "service_request_id": self.service_request_id,
            "title": self.title,
            "description": self.description,
            "agreed_amount_cents": self.agreed_amount_cents,
            "agreed_amount_kes": self.agreed_amount_cents / 100,
            "platform_fee_cents": self.platform_fee_cents,
            "platform_fee_kes": self.platform_fee_cents / 100,
            "fundi_amount_cents": self.fundi_amount_cents,
            "fundi_amount_kes": self.fundi_amount_cents / 100,
            "status": self.status,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "has_review": self.review is not None,
            "has_dispute": self.dispute is not None,
            "escrow_status": self.escrow_transaction.status if self.escrow_transaction else None,
        }
