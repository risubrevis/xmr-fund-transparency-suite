import uuid
from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

# --- Wallet schemas ---


class WalletCreate(BaseModel):
    """Request body for creating a new wallet."""

    name: str = Field(..., min_length=1, max_length=255)
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


class WalletUpdate(BaseModel):
    """Request body for updating a wallet."""

    name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None


class WalletResponse(BaseModel):
    """Wallet data returned in API responses."""

    id: uuid.UUID
    uuid: str
    name: str
    primary_address: str
    start_height: int
    last_scan_at: datetime | None = None
    last_scanned_height: int | None = None
    scan_error: str | None = None
    is_active: bool
    created_at: datetime

    @model_validator(mode="after")
    def normalize_empty_strings(self) -> "WalletResponse":
        if self.scan_error == "":
            self.scan_error = None
        return self

    model_config = {"from_attributes": True}


# --- Fund schemas ---


class FundCreate(BaseModel):
    """Request body for creating a new fund."""

    wallet_id: uuid.UUID = Field(
        ..., description="ID of the wallet this fund belongs to."
    )
    label: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(
        None,
        max_length=2048,
        description="Optional fund description displayed in the public widget.",
    )
    deposit_address: str = Field(
        ...,
        min_length=95,
        max_length=95,
        description="Deposit address for this fund. Must be unique across all funds.",
    )
    target_amount_xmr: Decimal | None = Field(
        None,
        description="Optional fundraising target in XMR",
    )
    widget_background_color: str | None = Field(
        None,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Optional hex color for widget background (e.g. #667eea).",
    )
    widget_text_color: str | None = Field(
        None,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Optional hex color for widget text (e.g. #ffffff).",
    )
    public_website: str | None = Field(
        None,
        max_length=255,
        description="Public website URL for the fund (without https://, e.g. example.com).",
    )

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

    @field_validator("deposit_address")
    @classmethod
    def validate_deposit_address_format(cls, v: str) -> str:
        import re

        if not re.match(r"^[48AB][1-9A-HJ-NP-Za-km-z]{94}$", v):
            raise ValueError("Invalid Monero deposit address format")
        return v

    @field_validator("public_website")
    @classmethod
    def validate_public_website(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            # Strip leading https:// or http:// if user accidentally included it
            if v.startswith("https://"):
                v = v[len("https://") :]
            elif v.startswith("http://"):
                v = v[len("http://") :]
            # Strip trailing slash
            v = v.rstrip("/")
            if not v:
                return None
        return v


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
    widget_background_color: str | None = Field(
        None,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Hex color for widget background (e.g. #667eea). Set to null to clear.",
    )
    widget_text_color: str | None = Field(
        None,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Hex color for widget text (e.g. #ffffff). Set to null to clear.",
    )
    public_website: str | None = Field(
        None,
        max_length=255,
        description="Public website URL for the fund (without https://, e.g. example.com).",
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

    @field_validator("public_website")
    @classmethod
    def validate_public_website(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if v.startswith("https://"):
                v = v[len("https://") :]
            elif v.startswith("http://"):
                v = v[len("http://") :]
            v = v.rstrip("/")
            if not v:
                return None
        return v


class FundResponse(BaseModel):
    """Fund data returned in API responses."""

    id: uuid.UUID
    public_uuid: str
    wallet_id: uuid.UUID
    label: str
    description: str | None = None
    deposit_address: str
    is_active: bool
    target_amount_xmr: Decimal | None = None
    widget_background_color: str | None = None
    widget_text_color: str | None = None
    public_website: str | None = None
    created_at: datetime

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


class LocaleUpdate(BaseModel):
    """Request body for updating the UI locale."""

    locale: str


class LocaleResponse(BaseModel):
    """Response for the locale setting."""

    locale: str


class PostCreate(BaseModel):
    """Request body for creating a new post."""

    body: str = Field(..., min_length=1, max_length=2048)
    fund_id: uuid.UUID | None = Field(
        None,
        description="Fund ID to link the post to. If not provided, fund_id query param is used.",
    )
    giveaway_id: uuid.UUID | None = Field(
        None,
        description="Giveaway ID to link the post to. Alternative to fund_id.",
    )


class PostUpdate(BaseModel):
    """Request body for updating a post."""

    body: str | None = Field(None, min_length=1, max_length=2048)
    fund_id: uuid.UUID | None = Field(
        None,
        description="Move post to a fund. Also updates wallet_id accordingly.",
    )
    giveaway_id: uuid.UUID | None = Field(
        None,
        description="Move post to a giveaway. Alternative to fund_id.",
    )


class PostResponse(BaseModel):
    """Post data returned in API responses."""

    id: uuid.UUID
    fund_id: uuid.UUID | None = None
    giveaway_id: uuid.UUID | None = None
    wallet_id: uuid.UUID
    body: str
    fund_label: str | None = None
    giveaway_title: str | None = None
    wallet_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class FilterMetadata(BaseModel):
    """Metadata describing active filters for export reports."""

    date_range: dict | None = None
    tiers: list[dict] | None = None
    sort: list[dict] | None = None


# --- Giveaway schemas ---


def _validate_monero_address(v: str) -> str:
    import re

    if not re.match(r"^[48AB][1-9A-HJ-NP-Za-km-z]{94}$", v):
        raise ValueError("Invalid Monero deposit address format")
    return v


def _normalize_public_website(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    if v.startswith("https://"):
        v = v[len("https://") :]
    elif v.startswith("http://"):
        v = v[len("http://") :]
    v = v.rstrip("/")
    return v or None


class GiveawayCreate(BaseModel):
    """Request body for creating a new giveaway."""

    wallet_id: uuid.UUID = Field(
        ..., description="ID of the wallet this giveaway belongs to."
    )
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(
        None,
        max_length=4096,
        description="Optional public description or prize details.",
    )
    deposit_address: str = Field(
        ...,
        min_length=95,
        max_length=95,
        description="Unique Monero sub-address dedicated to this giveaway.",
    )
    min_amount_xmr: Decimal = Field(
        ...,
        description="Minimum XMR transaction amount required to qualify for entry.",
    )
    start_date: datetime
    end_date: datetime
    instructions_after_end: str | None = Field(
        None,
        max_length=4096,
        description="Instructions for the winner shown once the giveaway closes.",
    )
    widget_background_color: str | None = Field(
        None,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Optional hex color for widget background.",
    )
    widget_text_color: str | None = Field(
        None,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Optional hex color for widget text.",
    )
    public_website: str | None = Field(
        None,
        max_length=255,
        description="Public website URL (without https://, e.g. example.com).",
    )

    @field_validator("deposit_address")
    @classmethod
    def validate_deposit_address_format(cls, v: str) -> str:
        return _validate_monero_address(v)

    @field_validator("min_amount_xmr")
    @classmethod
    def validate_min_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Minimum amount must be greater than 0")
        exponent = v.as_tuple().exponent
        if isinstance(exponent, int) and -exponent > 12:
            raise ValueError(
                "Minimum amount must not exceed 12 decimal places (XMR precision)"
            )
        return v

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        start = info.data.get("start_date")
        if start is not None and v <= start:
            raise ValueError("end_date must be after start_date")
        # A giveaway cannot be created with an end date in the past or now.
        if v <= datetime.now(timezone.utc):
            raise ValueError("end_date must be in the future")
        return v

    @field_validator("public_website")
    @classmethod
    def validate_public_website(cls, v: str | None) -> str | None:
        return _normalize_public_website(v)


class GiveawayUpdate(BaseModel):
    """Request body for updating a giveaway (only before it is closed)."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=4096)
    is_active: bool | None = None
    deposit_address: str | None = Field(
        None,
        min_length=95,
        max_length=95,
        description="Changing this resets recorded transactions for the giveaway.",
    )
    min_amount_xmr: Decimal | None = Field(None)
    start_date: datetime | None = None
    end_date: datetime | None = None
    instructions_after_end: str | None = Field(None, max_length=4096)
    widget_background_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    widget_text_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    public_website: str | None = Field(None, max_length=255)

    @field_validator("deposit_address")
    @classmethod
    def validate_deposit_address_format(cls, v: str | None) -> str | None:
        if v is not None:
            return _validate_monero_address(v)
        return v

    @field_validator("min_amount_xmr")
    @classmethod
    def validate_min_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is not None:
            if v <= 0:
                raise ValueError("Minimum amount must be greater than 0")
            exponent = v.as_tuple().exponent
            if isinstance(exponent, int) and -exponent > 12:
                raise ValueError(
                    "Minimum amount must not exceed 12 decimal places (XMR precision)"
                )
        return v

    @field_validator("public_website")
    @classmethod
    def validate_public_website(cls, v: str | None) -> str | None:
        return _normalize_public_website(v)

    @model_validator(mode="after")
    def validate_dates_consistency(self) -> "GiveawayUpdate":
        if self.start_date is not None and self.end_date is not None:
            if self.end_date <= self.start_date:
                raise ValueError("end_date must be after start_date")
        return self


class GiveawayWinnerInfo(BaseModel):
    """Public winner announcement data (present when is_closed)."""

    winning_txid: str | None = None
    winning_amount_xmr: Decimal | None = None
    winning_timestamp: datetime | None = None
    winning_block_height: int | None = None
    winning_block_hash: str | None = None
    eligible_count: int = 0


class GiveawayStats(BaseModel):
    """Aggregated statistics for a giveaway."""

    total_received_xmr: Decimal
    transaction_count: int
    eligible_count: int
    last_tx_at: datetime | None = None


class GiveawayResponse(BaseModel):
    """Giveaway data returned in API responses."""

    id: uuid.UUID
    public_uuid: str
    wallet_id: uuid.UUID
    title: str
    description: str | None = None
    deposit_address: str
    min_amount_xmr: Decimal
    start_date: datetime
    end_date: datetime
    instructions_after_end: str | None = None
    is_active: bool = True
    widget_background_color: str | None = None
    widget_text_color: str | None = None
    public_website: str | None = None
    is_closed: bool = False
    winning_block_hash: str | None = None
    winning_block_height: int | None = None
    # Lifecycle status computed by the backend: scheduled | active | ended | closed.
    status: str = "scheduled"
    created_at: datetime

    model_config = {"from_attributes": True}


class GiveawayDetailResponse(GiveawayResponse):
    """Full giveaway response including stats and winner info."""

    stats: GiveawayStats | None = None
    winner: GiveawayWinnerInfo | None = None
