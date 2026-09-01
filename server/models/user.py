"""User model for Fundi Connect."""

import uuid
from datetime import UTC, datetime

import bcrypt
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.extensions import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(db.Model):
    """User account model supporting customers, fundis, and administrators."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="customer"
    )  # customer, fundi, admin
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    fundi_profile = relationship(
        "FundiProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    wallet = relationship(
        "Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    customer_bookings = relationship(
        "Booking", foreign_keys="Booking.customer_id", back_populates="customer"
    )
    fundi_bookings = relationship(
        "Booking", foreign_keys="Booking.fundi_id", back_populates="fundi"
    )
    service_requests = relationship("ServiceRequest", back_populates="customer")
    customer_reviews = relationship(
        "Review", foreign_keys="Review.customer_id", back_populates="customer"
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Hash and store the user's password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify the password against the stored hash."""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))

    def is_fundi(self) -> bool:
        return self.role == "fundi"

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_customer(self) -> bool:
        return self.role == "customer"

    def to_dict(self, include_profile: bool = True) -> dict:
        """Serialize user to dict."""
        data = {
            "id": self.id,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_profile and self.is_fundi() and self.fundi_profile:
            data["fundi_profile"] = self.fundi_profile.to_dict()
        return data
