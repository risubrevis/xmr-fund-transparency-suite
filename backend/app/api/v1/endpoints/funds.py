import uuid

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.logging import get_logger
from app.models import Fund, Post, Transaction, Wallet
from app.reports.png_widget import generate_widget_png, FORMATS
from app.schemas import (
    FundCreate,
    FundDetailResponse,
    FundResponse,
    FundStats,
    FundUpdate,
)

logger = get_logger("api.funds")

router = APIRouter()


@router.get("/funds", response_model=list[FundDetailResponse])
async def list_funds(
    wallet_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> list[FundDetailResponse]:
    """List all funds, optionally filtered by wallet.

    When wallet_id is provided, includes aggregated statistics for each fund.
    """
    query = select(Fund).order_by(Fund.created_at)
    if wallet_id is not None:
        query = query.where(Fund.wallet_id == wallet_id)
    result = await db.execute(query)
    funds = result.scalars().all()

    responses = []
    for fund in funds:
        stats_result = await db.execute(
            select(
                func.coalesce(func.sum(Transaction.amount_xmr), 0).label("total"),
                func.count(Transaction.id).label("count"),
                func.max(Transaction.timestamp).label("last_tx"),
            ).where(Transaction.fund_id == fund.id)
        )
        row = stats_result.one()
        stats = FundStats(
            total_received_xmr=row.total,
            transaction_count=row.count,
            last_tx_at=row.last_tx,
        )
        responses.append(
            FundDetailResponse(
                id=fund.id,
                public_uuid=fund.public_uuid,
                wallet_id=fund.wallet_id,
                label=fund.label,
                description=fund.description,
                deposit_address=fund.deposit_address,
                is_active=fund.is_active,
                target_amount_xmr=fund.target_amount_xmr,
                widget_background_color=fund.widget_background_color,
                widget_text_color=fund.widget_text_color,
                public_website=fund.public_website,
                created_at=fund.created_at,
                stats=stats,
            )
        )

    return responses


@router.post("/funds", response_model=FundDetailResponse, status_code=201)
async def create_fund(
    body: FundCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> FundDetailResponse:
    """Create a new fund linked to a wallet."""
    # Verify the wallet exists
    result = await db.execute(select(Wallet).where(Wallet.id == body.wallet_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Verify deposit_address is unique
    existing = await db.execute(
        select(Fund).where(Fund.deposit_address == body.deposit_address)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="A fund with this deposit address already exists.",
        )

    fund = Fund(
        wallet_id=body.wallet_id,
        label=body.label,
        description=body.description,
        deposit_address=body.deposit_address,
        target_amount_xmr=body.target_amount_xmr,
        widget_background_color=body.widget_background_color,
        widget_text_color=body.widget_text_color,
        public_website=body.public_website,
    )
    db.add(fund)
    await db.commit()
    await db.refresh(fund)

    logger.info(
        "fund_created",
        fund_id=str(fund.id),
        wallet_id=str(fund.wallet_id),
        label=fund.label,
    )

    # A newly created fund has zero stats
    stats = FundStats(
        total_received_xmr=Decimal("0"),
        transaction_count=0,
        last_tx_at=None,
    )

    return FundDetailResponse(
        id=fund.id,
        public_uuid=fund.public_uuid,
        wallet_id=fund.wallet_id,
        label=fund.label,
        description=fund.description,
        deposit_address=fund.deposit_address,
        is_active=fund.is_active,
        target_amount_xmr=fund.target_amount_xmr,
        widget_background_color=fund.widget_background_color,
        widget_text_color=fund.widget_text_color,
        public_website=fund.public_website,
        created_at=fund.created_at,
        stats=stats,
    )


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
        wallet_id=fund.wallet_id,
        label=fund.label,
        description=fund.description,
        deposit_address=fund.deposit_address,
        is_active=fund.is_active,
        target_amount_xmr=fund.target_amount_xmr,
        widget_background_color=fund.widget_background_color,
        widget_text_color=fund.widget_text_color,
        public_website=fund.public_website,
        created_at=fund.created_at,
        stats=stats,
    )

    return response


@router.patch("/funds/{fund_id}", response_model=FundDetailResponse)
async def update_fund(
    fund_id: uuid.UUID,
    body: FundUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> FundResponse:
    """Update fund label, description, active status, deposit address, or target."""
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()

    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Use exclude_unset to distinguish "not provided" from "explicitly null"
    unset_fields = body.model_fields_set
    if body.label is not None:
        fund.label = body.label
    if body.is_active is not None:
        fund.is_active = body.is_active
    if "target_amount_xmr" in unset_fields:
        fund.target_amount_xmr = body.target_amount_xmr
    if "description" in unset_fields:
        fund.description = body.description
    if "widget_background_color" in unset_fields:
        fund.widget_background_color = body.widget_background_color
    if "widget_text_color" in unset_fields:
        fund.widget_text_color = body.widget_text_color
    if "public_website" in unset_fields:
        fund.public_website = body.public_website

    # Changing deposit_address resets scan history for the associated wallet
    if "deposit_address" in unset_fields and body.deposit_address is not None:
        if body.deposit_address != fund.deposit_address:
            # Check uniqueness
            existing = await db.execute(
                select(Fund).where(
                    Fund.deposit_address == body.deposit_address,
                    Fund.id != fund_id,
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail="A fund with this deposit address already exists.",
                )

            logger.info(
                "deposit_address_changed",
                fund_id=str(fund.id),
                old_address=fund.deposit_address[:12] + "...",
                new_address=body.deposit_address[:12] + "...",
            )
            # Delete all transactions for this fund (they were for the old address)
            await db.execute(
                Transaction.__table__.delete().where(Transaction.fund_id == fund_id)
            )
            # Reset wallet scan progress so the scanner re-scans
            wallet_result = await db.execute(
                select(Wallet).where(Wallet.id == fund.wallet_id)
            )
            wallet = wallet_result.scalar_one_or_none()
            if wallet:
                wallet.last_scanned_height = None
                wallet.last_scan_at = None
                wallet.scan_error = None

            fund.deposit_address = body.deposit_address
            logger.info(
                "scan_reset_for_deposit_address",
                fund_id=str(fund.id),
            )
        else:
            fund.deposit_address = body.deposit_address

    await db.commit()
    await db.refresh(fund)

    logger.info("fund_updated", fund_id=str(fund.id), label=fund.label)

    # Compute stats for the updated fund
    stats_result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_xmr), 0).label("total"),
            func.count(Transaction.id).label("count"),
            func.max(Transaction.timestamp).label("last_tx"),
        ).where(Transaction.fund_id == fund.id)
    )
    row = stats_result.one()
    stats = FundStats(
        total_received_xmr=row.total,
        transaction_count=row.count,
        last_tx_at=row.last_tx,
    )

    return FundDetailResponse(
        id=fund.id,
        public_uuid=fund.public_uuid,
        wallet_id=fund.wallet_id,
        label=fund.label,
        description=fund.description,
        deposit_address=fund.deposit_address,
        is_active=fund.is_active,
        target_amount_xmr=fund.target_amount_xmr,
        widget_background_color=fund.widget_background_color,
        widget_text_color=fund.widget_text_color,
        public_website=fund.public_website,
        created_at=fund.created_at,
        stats=stats,
    )


@router.delete("/funds/{fund_id}", status_code=204)
async def delete_fund(
    fund_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> None:
    """Delete a fund and all its transactions and posts."""
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()

    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Delete transactions and posts first (cascade should handle this, but be explicit)
    await db.execute(
        Transaction.__table__.delete().where(Transaction.fund_id == fund_id)
    )
    await db.execute(Post.__table__.delete().where(Post.fund_id == fund_id))
    await db.delete(fund)
    await db.commit()

    logger.info("fund_deleted", fund_id=str(fund_id))


@router.get("/funds/{fund_id}/widget-png")
async def download_widget_png(
    fund_id: uuid.UUID,
    format: str = Query(
        "wide", description="Image format: business_card, wide, vertical"
    ),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> Response:
    """Download widget as a PNG image in the specified format."""
    if format not in FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Choose from: {', '.join(FORMATS.keys())}",
        )

    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Fetch wallet for colors fallback
    wallet_result = await db.execute(select(Wallet).where(Wallet.id == fund.wallet_id))
    wallet = wallet_result.scalar_one_or_none()

    # Calculate total received
    total_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount_xmr), 0)).where(
            Transaction.fund_id == fund.id
        )
    )
    total_xmr = total_result.scalar()

    # Resolve colors with fallbacks to defaults
    base_color = fund.widget_background_color or "#667eea"
    text_color = fund.widget_text_color or "#ffffff"

    png_bytes = generate_widget_png(
        label=fund.label,
        description=fund.description,
        public_website=fund.public_website,
        deposit_address=fund.deposit_address,
        target_amount_xmr=str(fund.target_amount_xmr)
        if fund.target_amount_xmr
        else None,
        total_received_xmr=f"{total_xmr:.4f}",
        base_color=base_color,
        text_color=text_color,
        format_type=format,
    )

    fmt_info = FORMATS[format]
    filename = f"{fund.label.replace(' ', '_')}_{format}.png"

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
