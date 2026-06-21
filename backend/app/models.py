import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Fund(Base):
    """A tracked Monero view-only wallet / fund."""

    __tablename__ = "funds"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    public_uuid: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_address: Mapped[str] = mapped_column(String(95), nullable=False)
    deposit_address: Mapped[str | None] = mapped_column(String(95), nullable=True)
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
    target_amount_xmr: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=20, scale=12), nullable=True
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="fund", lazy="selectin"
    )


class Transaction(Base):
    """An incoming Monero transaction for a fund."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fund_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("funds.id"), nullable=False)
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
