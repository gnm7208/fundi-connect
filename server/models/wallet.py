"""Wallet and Transaction models for Fundi Connect."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.extensions import db


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Wallet(db.Model):
    """Fundi wallet holding earned balance."""

    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    balance_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="KES")
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship(
        "WalletTransaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
        order_by="desc(WalletTransaction.created_at)",
    )

    def to_dict(self, include_transactions: bool = False) -> dict:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "balance_cents": self.balance_cents,
            "balance_kes": self.balance_cents / 100,
            "currency": self.currency,
            "is_frozen": self.is_frozen,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_transactions:
            data["transactions"] = [tx.to_dict() for tx in self.transactions]
        return data


class WalletTransaction(db.Model):
    """Immutable ledger entry for wallet balance modifications."""

    __tablename__ = "wallet_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    wallet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Types: escrow_payout (credit), withdrawal (debit), refund (credit), adjustment (credit/debit)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount_cents: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # positive for credit, negative for debit
    balance_after_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    reference: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # booking id or mpesa reference
    status: Mapped[str] = mapped_column(
        String(20), default="completed"
    )  # completed, pending, failed
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "wallet_id": self.wallet_id,
            "type": self.type,
            "amount_cents": self.amount_cents,
            "amount_kes": self.amount_cents / 100,
            "balance_after_cents": self.balance_after_cents,
            "balance_after_kes": self.balance_after_cents / 100,
            "reference": self.reference,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
