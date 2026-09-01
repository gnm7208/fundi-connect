"""Service Request and Quote models for Fundi Connect."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.extensions import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class ServiceRequest(db.Model):
    """Customer job posting/request for quotes (RFQ)."""

    __tablename__ = "service_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Location
    location_name: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Budget & Timing
    budget_min_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_max_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default="open"
    )  # open, matched, cancelled, closed

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    customer = relationship("User", back_populates="service_requests")
    category = relationship("Category", back_populates="service_requests")
    quotes = relationship("Quote", back_populates="service_request", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="service_request")

    def to_dict(self, include_quotes: bool = False) -> dict:
        data = {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.full_name if self.customer else None,
            "customer_phone": self.customer.phone if self.customer else None,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "title": self.title,
            "description": self.description,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "budget_min_cents": self.budget_min_cents,
            "budget_max_cents": self.budget_max_cents,
            "budget_min_kes": (self.budget_min_cents / 100) if self.budget_min_cents else None,
            "budget_max_kes": (self.budget_max_cents / 100) if self.budget_max_cents else None,
            "preferred_date": self.preferred_date.isoformat() if self.preferred_date else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "quote_count": len(self.quotes),
        }
        if include_quotes:
            data["quotes"] = [quote.to_dict() for quote in self.quotes]
        return data


class Quote(db.Model):
    """Bid or price quote submitted by a fundi for a service request."""

    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    service_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False
    )
    fundi_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, accepted, declined
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    service_request = relationship("ServiceRequest", back_populates="quotes")
    fundi = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "service_request_id": self.service_request_id,
            "fundi_id": self.fundi_id,
            "fundi_name": self.fundi.full_name if self.fundi else None,
            "fundi_rating": (
                self.fundi.fundi_profile.rating_avg
                if self.fundi and self.fundi.fundi_profile
                else None
            ),
            "amount_cents": self.amount_cents,
            "amount_kes": self.amount_cents / 100,
            "estimated_hours": self.estimated_hours,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
