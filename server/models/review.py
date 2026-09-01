"""Review model for Fundi Connect."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.extensions import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Review(db.Model):
    """Verified customer rating and review submitted after completed escrow booking."""

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    booking_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    fundi_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fundi_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 stars
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    booking = relationship("Booking", back_populates="review")
    customer = relationship("User", foreign_keys=[customer_id], back_populates="customer_reviews")
    fundi = relationship("FundiProfile", foreign_keys=[fundi_id], back_populates="reviews")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.full_name if self.customer else None,
            "fundi_id": self.fundi_id,
            "rating": self.rating,
            "review_text": self.review_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
