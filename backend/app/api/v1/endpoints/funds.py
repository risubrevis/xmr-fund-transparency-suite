import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.config import settings
from app.crypto import ViewKeyEncryption, validate_fund_input
from app.database import get_db
from app.logging import get_logger
from app.models import Fund, Transaction
from app.rpc_client import WalletRPCError, close_wallet, create_view_only_wallet
from app.schemas import (
    FundCreate,
    FundDetailResponse,
    FundResponse,
    FundStats,
    FundUpdate,
)

logger = get_logger("api.funds")

router = APIRouter()


@router.get("/funds", response_model=list[FundResponse])
async def list_funds(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> list[FundResponse]:
    """List all funds (one wallet per instance, so max 1)."""
    result = await db.execute(select(Fund).order_by(Fund.created_at))
    funds = result.scalars().all()
    return [FundResponse.model_validate(f) for f in funds]


def _get_encryption() -> ViewKeyEncryption:
    return ViewKeyEncryption(settings.view_key_master_secret)


@router.post("/funds", response_model=FundResponse, status_code=201)
async def create_fund(
    body: FundCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> FundResponse:
    """Create a new fund (view-only wallet tracker)."""
    validate_fund_input(body.primary_address, body.view_key, body.deposit_address)

    # Check if a fund already exists (one wallet per instance)
    existing = await db.execute(select(Fund).where(Fund.is_active.is_(True)))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="An active fund already exists. Only one wallet per instance is supported.",
        )

    # Also check if any fund exists at all (including inactive)
    any_fund = await db.execute(select(Fund))
    if any_fund.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="A fund already exists. Delete it first before creating a new one.",
        )

    # Create view-only wallet on monero-wallet-rpc
    try:
        await create_view_only_wallet(
            address=body.primary_address,
            view_key=body.view_key,
            start_height=body.start_height,
        )
    except WalletRPCError as e:
        logger.error("rpc_wallet_creation_failed", error=str(e))
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )
    except Exception as e:
        logger.error("rpc_wallet_creation_failed", error=str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected error creating wallet: {str(e)}",
        )

    # Encrypt view key before storing
    cipher = _get_encryption()
    encrypted_view_key = cipher.encrypt(body.view_key)

    fund = Fund(
        label=body.label,
        primary_address=body.primary_address,
        deposit_address=body.deposit_address,
        view_key=encrypted_view_key,
        start_height=body.start_height,
        target_amount_xmr=body.target_amount_xmr,
    )
    db.add(fund)
    await db.commit()
    await db.refresh(fund)

    logger.info(
        "fund_created",
        fund_id=str(fund.id),
        label=fund.label,
        start_height=fund.start_height,
    )

    return FundResponse.model_validate(fund)


@router.get("/funds/{fund_id}", response_model=FundDetailResponse)
async def get_fund(
    fund_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> FundDetailResponse:
    """Get fund status with aggregated statistics."""
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()

    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Compute stats
    stats_result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_xmr), 0).label("total"),
            func.count(Transaction.id).label("count"),
            func.max(Transaction.timestamp).label("last_tx"),
        ).where(Transaction.fund_id == fund_id)
    )
    row = stats_result.one()

    stats = FundStats(
        total_received_xmr=row.total,
        transaction_count=row.count,
        last_tx_at=row.last_tx,
    )

    response = FundDetailResponse(
        id=fund.id,
        public_uuid=fund.public_uuid,
        label=fund.label,
        primary_address=fund.primary_address,
        deposit_address=fund.deposit_address,
        start_height=fund.start_height,
        is_active=fund.is_active,
        target_amount_xmr=fund.target_amount_xmr,
        last_scan_at=fund.last_scan_at,
        last_scanned_height=fund.last_scanned_height,
        scan_error=fund.scan_error,
        created_at=fund.created_at,
        stats=stats,
    )

    return response


@router.patch("/funds/{fund_id}", response_model=FundResponse)
async def update_fund(
    fund_id: uuid.UUID,
    body: FundUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> FundResponse:
    """Update fund label or active status."""
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()

    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    if body.label is not None:
        fund.label = body.label
    if body.is_active is not None:
        fund.is_active = body.is_active

    # Use exclude_unset to distinguish "not provided" from "explicitly null"
    unset_fields = body.model_fields_set
    if "target_amount_xmr" in unset_fields:
        fund.target_amount_xmr = body.target_amount_xmr

    await db.commit()
    await db.refresh(fund)

    logger.info("fund_updated", fund_id=str(fund.id), label=fund.label)

    return FundResponse.model_validate(fund)


@router.delete("/funds/{fund_id}", status_code=204)
async def delete_fund(
    fund_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> None:
    """Delete a fund and all its transactions."""
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()

    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Delete transactions first
    await db.execute(
        Transaction.__table__.delete().where(Transaction.fund_id == fund_id)
    )
    await db.delete(fund)
    await db.commit()

    # Close the wallet on monero-wallet-rpc so the next fund can create a fresh one
    try:
        await close_wallet()
    except Exception as e:
        logger.warning("wallet_close_after_delete_failed", error=str(e))

    logger.info("fund_deleted", fund_id=str(fund_id))
