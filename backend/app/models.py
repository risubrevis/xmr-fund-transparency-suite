from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Wallet(Base):
    """A Monero view-only wallet tracked by the application."""

    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_address: Mapped[str] = mapped_column(String(95), nullable=False)
    view_key: Mapped[str] = mapped_column(
        String(512), nullable=False
    )  # encrypted, potentially longer than 64 chars
    start_height: Mapped[int] = mapped_column(nullable=False)
    last_scanned_height: Mapped[int | None] = mapped_column(nullable=True)
    last_scan_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scan_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    funds: Mapped[list["Fund"]] = relationship(
        back_populates="wallet", lazy="selectin", cascade="all, delete-orphan"
    )
    giveaways: Mapped[list["Giveaway"]] = relationship(
        back_populates="wallet", lazy="selectin", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="wallet", lazy="selectin"
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="wallet", lazy="selectin", cascade="all, delete-orphan"
    )


class Fund(Base):
    """A fund tied to a wallet, identified by its deposit address."""

    __tablename__ = "funds"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    public_uuid: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    deposit_address: Mapped[str] = mapped_column(
        String(95), unique=True, nullable=False
    )
    target_amount_xmr: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=20, scale=12), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    widget_background_color: Mapped[str | None] = mapped_column(
        String(7), nullable=True
    )
    widget_text_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    public_website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    wallet: Mapped["Wallet"] = relationship(back_populates="funds")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="fund", lazy="selectin", cascade="all, delete-orphan"
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="fund", lazy="selectin", cascade="all, delete-orphan"
    )


class Giveaway(Base):
    """A provably-fair raffle tied to a wallet's deposit address.

    Like a Fund it records incoming transactions to its deposit_address,
    but has bounded campaign dates and a deterministic winner selection
    seeded by a future Monero block hash.
    """

    __tablename__ = "giveaways"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    public_uuid: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    deposit_address: Mapped[str] = mapped_column(
        String(95), unique=True, nullable=False
    )
    min_amount_xmr: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=12), nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    instructions_after_end: Mapped[str | None] = mapped_column(
        String(4096), nullable=True
    )
    widget_background_color: Mapped[str | None] = mapped_column(
        String(7), nullable=True
    )
    widget_text_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    public_website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    winning_transaction_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    winning_block_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    winning_block_height: Mapped[int | None] = mapped_column(nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    wallet: Mapped["Wallet"] = relationship(back_populates="giveaways")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="giveaway",
        lazy="selectin",
        cascade="all, delete-orphan",
        foreign_keys="Transaction.giveaway_id",
    )
    posts: Mapped[list["Post"]] = relationship(
        back_populates="giveaway",
        lazy="selectin",
        cascade="all, delete-orphan",
        foreign_keys="Post.giveaway_id",
    )


class Transaction(Base):
    """An incoming Monero transaction for a fund or a giveaway."""

    __tablename__ = "transactions"
    __table_args__ = (
        # A transaction is linked to exactly one of a fund or a giveaway.
        CheckConstraint(
            "(fund_id IS NOT NULL AND giveaway_id IS NULL) "
            "OR (fund_id IS NULL AND giveaway_id IS NOT NULL)",
            name="tx_fund_xor_giveaway",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fund_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("funds.id", ondelete="CASCADE"), nullable=True
    )
    giveaway_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=True
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )
    txid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_xmr: Mapped[Decimal] = mapped_column(
        Numeric(precision=20, scale=12), nullable=False
    )
    confirmations: Mapped[int] = mapped_column(default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unlock_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    height: Mapped[int] = mapped_column(nullable=False, index=True)

    fund: Mapped["Fund | None"] = relationship(back_populates="transactions")
    giveaway: Mapped["Giveaway | None"] = relationship(
        back_populates="transactions", foreign_keys=[giveaway_id]
    )
    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")


class Post(Base):
    """A news/announcement post."""

    __tablename__ = "posts"
    __table_args__ = (
        # A post is linked to exactly one of a fund or a giveaway.
        CheckConstraint(
            "(fund_id IS NOT NULL AND giveaway_id IS NULL) "
            "OR (fund_id IS NULL AND giveaway_id IS NOT NULL)",
            name="post_fund_xor_giveaway",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fund_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("funds.id", ondelete="CASCADE"), nullable=True
    )
    giveaway_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=True
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(String(2048), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    fund: Mapped["Fund | None"] = relationship(back_populates="posts")
    giveaway: Mapped["Giveaway | None"] = relationship(
        back_populates="posts", foreign_keys=[giveaway_id]
    )
    wallet: Mapped["Wallet"] = relationship(back_populates="posts")
