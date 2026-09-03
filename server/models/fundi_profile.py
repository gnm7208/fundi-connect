"""Fundi profile and skill models for Fundi Connect."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.extensions import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class FundiProfile(db.Model):
    """Profile data and verification details for verified craftspeople."""

    __tablename__ = "fundi_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    business_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=1)

    # Verification Details
    id_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    id_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, verified, rejected
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Location & Coverage
    location_name: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )  # e.g. "Kilimani, Nairobi"
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    service_radius_km: Mapped[float] = mapped_column(Float, default=15.0)

    # Pricing & Availability
    hourly_rate_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # in minor units KES cents
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    # Aggregated Reputation Metrics
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    jobs_completed: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    user = relationship("User", back_populates="fundi_profile")
    skills = relationship(
        "FundiSkill", back_populates="fundi_profile", cascade="all, delete-orphan"
    )
    reviews = relationship("Review", foreign_keys="Review.fundi_id", back_populates="fundi")

    def is_verified(self) -> bool:
        return self.verification_status == "verified"

    def to_dict(self, include_skills: bool = True, include_private: bool = False) -> dict:
        """Serialize the profile.

        `include_private` adds the owner-only verification fields; it must stay off
        for public search and profile responses so admin notes are not exposed.
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "business_name": self.business_name,
            "bio": self.bio,
            "experience_years": self.experience_years,
            "verification_status": self.verification_status,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "service_radius_km": self.service_radius_km,
            "hourly_rate_cents": self.hourly_rate_cents,
            "hourly_rate_kes": (self.hourly_rate_cents / 100) if self.hourly_rate_cents else None,
            "is_available": self.is_available,
            "rating_avg": round(self.rating_avg, 2),
            "rating_count": self.rating_count,
            "jobs_completed": self.jobs_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_skills:
            data["skills"] = [skill.to_dict() for skill in self.skills]
        if include_private:
            data["verification_notes"] = self.verification_notes
            data["id_number"] = self.id_number
            data["id_document_url"] = self.id_document_url
        return data


class FundiSkill(db.Model):
    """Specific skill or trade associated with a fundi profile."""

    __tablename__ = "fundi_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    fundi_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("fundi_profiles.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, default=1)
    certification_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    fundi_profile = relationship("FundiProfile", back_populates="skills")
    category = relationship("Category", back_populates="fundi_skills")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "category_slug": self.category.slug if self.category else None,
            "skill_name": self.skill_name,
            "experience_years": self.experience_years,
            "certification_url": self.certification_url,
        }
