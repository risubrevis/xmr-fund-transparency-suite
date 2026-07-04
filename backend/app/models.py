from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, func
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


class Transaction(Base):
    """An incoming Monero transaction for a fund."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fund_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("funds.id", ondelete="CASCADE"), nullable=False
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )
    txid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_xmr: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=12), nullable=False
    )
    confirmations: Mapped[int] = mapped_column(default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unlock_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    height: Mapped[int] = mapped_column(nullable=False, index=True)

    fund: Mapped["Fund"] = relationship(back_populates="transactions")
    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")


class Post(Base):
    """A news/announcement post."""

    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fund_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("funds.id", ondelete="CASCADE"), nullable=False
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

    fund: Mapped["Fund"] = relationship(back_populates="posts")
    wallet: Mapped["Wallet"] = relationship(back_populates="posts")
