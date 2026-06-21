import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


class FundCreate(BaseModel):
    """Request body for creating a new fund."""

    label: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(
        None,
        max_length=2048,
        description="Optional fund description displayed in the public widget.",
    )
    primary_address: str = Field(..., min_length=95, max_length=95)
    deposit_address: str | None = Field(
        None,
        min_length=95,
        max_length=95,
        description="Optional deposit address. Defaults to primary_address if not provided.",
    )
    view_key: str = Field(..., min_length=64, max_length=64)
    start_height: int = Field(..., ge=0)
    target_amount_xmr: Decimal | None = Field(
        None,
        description="Optional fundraising target in XMR",
    )

    @field_validator("target_amount_xmr")
    @classmethod
    def validate_target_amount_precision(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            if v <= 0:
                raise ValueError("Target amount must be greater than 0")
            # XMR has at most 12 decimal places (piconero precision)
            exponent = v.as_tuple().exponent
            if isinstance(exponent, int) and -exponent > 12:
                raise ValueError(
                    "Target amount must not exceed 12 decimal places (XMR precision)"
                )
        return v

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

    @field_validator("deposit_address")
    @classmethod
    def validate_deposit_address_format(cls, v: str | None) -> str | None:
        import re

        if v is not None and not re.match(r"^[48AB][1-9A-HJ-NP-Za-km-z]{94}$", v):
            raise ValueError("Invalid Monero deposit address format")
        return v

    @model_validator(mode="after")
    def default_deposit_address(self) -> "FundCreate":
        if self.deposit_address is None:
            self.deposit_address = self.primary_address
        return self


class FundUpdate(BaseModel):
    """Request body for updating a fund."""

    label: str | None = None
    description: str | None = Field(
        None,
        max_length=2048,
        description="Optional fund description. Set to null to clear.",
    )
    is_active: bool | None = None
    target_amount_xmr: Decimal | None = Field(
        None,
        description="Optional fundraising target in XMR. Set to null to clear.",
    )
    deposit_address: str | None = Field(
        None,
        min_length=95,
        max_length=95,
        description="Update the deposit address. Changing this will reset scan history and re-scan.",
    )

    @field_validator("deposit_address")
    @classmethod
    def validate_deposit_address_format(cls, v: str | None) -> str | None:
        import re

        if v is not None and not re.match(r"^[48AB][1-9A-HJ-NP-Za-km-z]{94}$", v):
            raise ValueError("Invalid Monero deposit address format")
        return v

    @field_validator("target_amount_xmr")
    @classmethod
    def validate_target_amount_precision(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            if v <= 0:
                raise ValueError("Target amount must be greater than 0")
            exponent = v.as_tuple().exponent
            if isinstance(exponent, int) and -exponent > 12:
                raise ValueError(
                    "Target amount must not exceed 12 decimal places (XMR precision)"
                )
        return v


class FundResponse(BaseModel):
    """Fund data returned in API responses."""

    id: uuid.UUID
    public_uuid: str
    label: str
    description: str | None = None
    primary_address: str
    deposit_address: str | None = None
    start_height: int
    is_active: bool
    target_amount_xmr: Decimal | None = None
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
    amount_atomic: int
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


class DateTimeFormatUpdate(BaseModel):
    """Request body for updating datetime format."""

    pattern: str


class DateTimeFormatResponse(BaseModel):
    """Response for datetime format setting."""

    pattern: str


class WidgetColorUpdate(BaseModel):
    """Request body for updating widget base color."""

    color: str


class WidgetColorResponse(BaseModel):
    """Response for widget color setting."""

    color: str


class WidgetTextColorUpdate(BaseModel):
    """Request body for updating widget text color."""

    color: str


class WidgetTextColorResponse(BaseModel):
    """Response for widget text color setting."""

    color: str


class FilterMetadata(BaseModel):
    """Metadata describing active filters for export reports."""

    date_range: dict | None = None
    tiers: list[dict] | None = None
    sort: list[dict] | None = None
