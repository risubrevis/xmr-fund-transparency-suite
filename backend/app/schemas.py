import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


class FundCreate(BaseModel):
    """Request body for creating a new fund."""

    label: str = Field(..., min_length=1, max_length=255)
    primary_address: str = Field(..., min_length=95, max_length=95)
    view_key: str = Field(..., min_length=64, max_length=64)
    start_height: int = Field(..., ge=0)

    @field_validator("view_key")
    @classmethod
    def validate_view_key_format(cls, v: str) -> str:
        import re

        if not re.match(r"^[0-9a-fA-F]{64}$", v):
            raise ValueError("View key must be 64 hexadecimal characters")
        return v.lower()

    @field_validator("primary_address")
    @classmethod
    def validate_address_format(cls, v: str) -> str:
        import re

        if not re.match(r"^[48AB][1-9A-HJ-NP-Za-km-z]{94}$", v):
            raise ValueError("Invalid Monero address format")
        return v


class FundUpdate(BaseModel):
    """Request body for updating a fund."""

    label: str | None = None
    is_active: bool | None = None


class FundResponse(BaseModel):
    """Fund data returned in API responses."""

    id: uuid.UUID
    public_uuid: str
    label: str
    primary_address: str
    start_height: int
    is_active: bool
    last_scan_at: datetime | None = None
    last_scanned_height: int | None = None
    scan_error: str | None = None
    created_at: datetime

    @model_validator(mode="after")
    def normalize_empty_strings(self) -> "FundResponse":
        if self.scan_error == "":
            self.scan_error = None
        return self

    model_config = {"from_attributes": True}


class FundStats(BaseModel):
    """Aggregated statistics for a fund."""

    total_received_xmr: Decimal
    transaction_count: int
    last_tx_at: datetime | None = None


class FundDetailResponse(FundResponse):
    """Full fund response including stats."""

    stats: FundStats | None = None


class TransactionResponse(BaseModel):
    """Transaction data returned in API responses."""

    id: uuid.UUID
    txid: str
    amount_xmr: Decimal
    confirmations: int
    timestamp: datetime
    height: int
    unlock_time: int | None = None

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""

    items: list[TransactionResponse]
    next_cursor: str | None = None
    has_more: bool = False
