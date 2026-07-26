"""Giveaway CRUD + provably-fair winner selection + widget helpers."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.fund_widget import _generate_qr_data_url
from app.auth import verify_api_key
from app.database import get_db
from app.daemon_rpc import DaemonRPCClient
from app.filters import (
    VALID_TIER_NAMES,
    build_date_filter,
    build_order_by,
    build_tier_filter,
    describe_filters,
    parse_sort,
)
from app.giveaway_selection import WinnerSelectionError, select_winner
from app.logging import get_logger
from app.models import Fund, Giveaway, Transaction, Wallet
from app.reports.csv_export import generate_csv_export
from app.reports.json_export import generate_json_export
from app.reports.pdf import generate_pdf_report
from app.reports.png_widget import FORMATS, WidgetFormat, generate_widget_png
from app.reports.xlsx import generate_xlsx_export
from app.reports.xml import generate_xml_report
from app.settings import get_datetime_format
from app.schemas import (
    GiveawayCreate,
    GiveawayDetailResponse,
    GiveawayStats,
    GiveawayUpdate,
    GiveawayWinnerInfo,
)

logger = get_logger("api.giveaways")

router = APIRouter()


async def _deposit_address_taken(
    db: AsyncSession, address: str, exclude_giveaway_id: uuid.UUID | None = None
) -> bool:
    """A deposit address must be unique across both funds and giveaways."""
    fund_hit = await db.execute(select(Fund.id).where(Fund.deposit_address == address))
    if fund_hit.scalar_one_or_none() is not None:
        return True
    gq = select(Giveaway.id).where(Giveaway.deposit_address == address)
    if exclude_giveaway_id is not None:
        gq = gq.where(Giveaway.id != exclude_giveaway_id)
    give_hit = await db.execute(gq)
    return give_hit.scalar_one_or_none() is not None


# Core fields that are locked once the giveaway has started (start_date <= now).
CORE_FIELDS = {"deposit_address", "min_amount_xmr", "start_date", "end_date"}


def _giveaway_status(giveaway: Giveaway, now: datetime | None = None) -> str:
    """Lifecycle status: scheduled | active | ended | closed."""
    if giveaway.is_closed:
        return "closed"
    now = now or datetime.now(timezone.utc)
    if now < giveaway.start_date:
        return "scheduled"
    if now < giveaway.end_date:
        return "active"
    return "ended"


def _to_detail(
    giveaway: Giveaway,
    stats: GiveawayStats,
    winner: GiveawayWinnerInfo | None,
) -> GiveawayDetailResponse:
    return GiveawayDetailResponse(
        id=giveaway.id,
        public_uuid=giveaway.public_uuid,
        wallet_id=giveaway.wallet_id,
        title=giveaway.title,
        description=giveaway.description,
        deposit_address=giveaway.deposit_address,
        min_amount_xmr=giveaway.min_amount_xmr,
        start_date=giveaway.start_date,
        end_date=giveaway.end_date,
        instructions_after_end=giveaway.instructions_after_end,
        is_active=giveaway.is_active,
        widget_background_color=giveaway.widget_background_color,
        widget_text_color=giveaway.widget_text_color,
        public_website=giveaway.public_website,
        is_closed=giveaway.is_closed,
        winning_block_hash=giveaway.winning_block_hash,
        winning_block_height=giveaway.winning_block_height,
        status=_giveaway_status(giveaway),
        created_at=giveaway.created_at,
        stats=stats,
        winner=winner,
    )


async def _compute_stats(db: AsyncSession, giveaway: Giveaway) -> GiveawayStats:
    rows = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_xmr), 0).label("total"),
            func.count(Transaction.id).label("count"),
            func.max(Transaction.timestamp).label("last_tx"),
        ).where(Transaction.giveaway_id == giveaway.id)
    )
    row = rows.one()
    eligible_rows = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.giveaway_id == giveaway.id,
            Transaction.timestamp >= giveaway.start_date,
            Transaction.timestamp <= giveaway.end_date,
            Transaction.amount_xmr >= Decimal(giveaway.min_amount_xmr),
        )
    )
    eligible_count = int(eligible_rows.scalar() or 0)
    return GiveawayStats(
        total_received_xmr=row.total,
        transaction_count=row._mapping["count"],
        eligible_count=eligible_count,
        last_tx_at=row.last_tx,
    )


async def _compute_winner(
    db: AsyncSession, giveaway: Giveaway
) -> GiveawayWinnerInfo | None:
    if not giveaway.is_closed:
        return None
    winner = None
    if giveaway.winning_transaction_id is not None:
        wres = await db.execute(
            select(Transaction).where(Transaction.id == giveaway.winning_transaction_id)
        )
        winner = wres.scalar_one_or_none()
    return GiveawayWinnerInfo(
        winning_txid=winner.txid if winner else None,
        winning_amount_xmr=winner.amount_xmr if winner else None,
        winning_timestamp=winner.timestamp if winner else None,
        winning_block_height=giveaway.winning_block_height,
        winning_block_hash=giveaway.winning_block_hash,
        eligible_count=0,
    )


@router.get("/giveaways", response_model=list[GiveawayDetailResponse])
async def list_giveaways(
    wallet_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> list[GiveawayDetailResponse]:
    """List all giveaways, optionally filtered by wallet, with stats."""
    query = select(Giveaway).order_by(Giveaway.created_at)
    if wallet_id is not None:
        query = query.where(Giveaway.wallet_id == wallet_id)
    result = await db.execute(query)
    giveaways = result.scalars().all()

    out: list[GiveawayDetailResponse] = []
    for g in giveaways:
        stats = await _compute_stats(db, g)
        winner = await _compute_winner(db, g)
        # Reflect eligible count in winner info too.
        if winner is not None:
            winner = winner.model_copy(update={"eligible_count": stats.eligible_count})
        out.append(_to_detail(g, stats, winner))
    return out


@router.post("/giveaways", response_model=GiveawayDetailResponse, status_code=201)
async def create_giveaway(
    body: GiveawayCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> GiveawayDetailResponse:
    """Create a new giveaway linked to a wallet."""
    wres = await db.execute(select(Wallet).where(Wallet.id == body.wallet_id))
    if wres.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Wallet not found")

    if await _deposit_address_taken(db, body.deposit_address):
        raise HTTPException(
            status_code=409,
            detail="A fund or giveaway with this deposit address already exists.",
        )

    giveaway = Giveaway(
        wallet_id=body.wallet_id,
        title=body.title,
        description=body.description,
        deposit_address=body.deposit_address,
        min_amount_xmr=body.min_amount_xmr,
        start_date=body.start_date,
        end_date=body.end_date,
        instructions_after_end=body.instructions_after_end,
        widget_background_color=body.widget_background_color,
        widget_text_color=body.widget_text_color,
        public_website=body.public_website,
    )
    db.add(giveaway)
    await db.commit()
    await db.refresh(giveaway)

    logger.info(
        "giveaway_created",
        giveaway_id=str(giveaway.id),
        wallet_id=str(giveaway.wallet_id),
        title=giveaway.title,
    )

    stats = GiveawayStats(
        total_received_xmr=Decimal("0"),
        transaction_count=0,
        eligible_count=0,
        last_tx_at=None,
    )
    return _to_detail(giveaway, stats, None)


@router.get("/giveaways/{giveaway_id}", response_model=GiveawayDetailResponse)
async def get_giveaway(
    giveaway_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> GiveawayDetailResponse:
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    giveaway = res.scalar_one_or_none()
    if not giveaway:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    stats = await _compute_stats(db, giveaway)
    winner = await _compute_winner(db, giveaway)
    if winner is not None:
        winner = winner.model_copy(update={"eligible_count": stats.eligible_count})
    return _to_detail(giveaway, stats, winner)


@router.patch("/giveaways/{giveaway_id}", response_model=GiveawayDetailResponse)
async def update_giveaway(
    giveaway_id: uuid.UUID,
    body: GiveawayUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> GiveawayDetailResponse:
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    giveaway = res.scalar_one_or_none()
    if not giveaway:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    if giveaway.is_closed:
        raise HTTPException(
            status_code=409,
            detail="Giveaway is closed and can no longer be edited.",
        )

    unset = body.model_fields_set
    now = datetime.now(timezone.utc)
    is_started = now >= giveaway.start_date  # active or ended

    # Core fields (deposit_address, min_amount_xmr, start_date, end_date) are
    # locked once the campaign has started — changing the rules mid-flight
    # would undermine the provably-fair eligibility pool.
    if is_started:
        attempted_core = CORE_FIELDS & unset
        if attempted_core:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Cannot change core fields "
                    f"({', '.join(sorted(attempted_core))}) after the giveaway "
                    "has started. Only title, description, instructions, colors, "
                    "public_website and is_active may be edited."
                ),
            )

    # Cosmetic fields — editable in every non-closed state.
    if body.title is not None:
        giveaway.title = body.title
    if "description" in unset:
        giveaway.description = body.description
    if body.is_active is not None and "is_active" in unset:
        giveaway.is_active = body.is_active
    if "instructions_after_end" in unset:
        giveaway.instructions_after_end = body.instructions_after_end
    if "widget_background_color" in unset:
        giveaway.widget_background_color = body.widget_background_color
    if "widget_text_color" in unset:
        giveaway.widget_text_color = body.widget_text_color
    if "public_website" in unset:
        giveaway.public_website = body.public_website

    # Core fields — only editable while scheduled (not yet started).
    if not is_started:
        new_start = (
            body.start_date
            if ("start_date" in unset and body.start_date is not None)
            else giveaway.start_date
        )
        new_end = (
            body.end_date
            if ("end_date" in unset and body.end_date is not None)
            else giveaway.end_date
        )
        if new_start >= new_end:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date.",
            )
        # end_date must remain in the future when editing a scheduled giveaway.
        if new_end <= now:
            raise HTTPException(
                status_code=400,
                detail="end_date must be in the future.",
            )

        if body.min_amount_xmr is not None and "min_amount_xmr" in unset:
            giveaway.min_amount_xmr = body.min_amount_xmr
        if body.start_date is not None and "start_date" in unset:
            giveaway.start_date = body.start_date
        if body.end_date is not None and "end_date" in unset:
            giveaway.end_date = body.end_date

        if "deposit_address" in unset and body.deposit_address is not None:
            if body.deposit_address != giveaway.deposit_address:
                if await _deposit_address_taken(
                    db, body.deposit_address, exclude_giveaway_id=giveaway.id
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="A fund or giveaway with this deposit address already exists.",
                    )
                # Wipe recorded transactions for the old address; rescan will refill.
                await db.execute(
                    delete(Transaction).where(
                        Transaction.giveaway_id == giveaway_id
                    )
                )
                wres = await db.execute(
                    select(Wallet).where(Wallet.id == giveaway.wallet_id)
                )
                wallet = wres.scalar_one_or_none()
                if wallet:
                    wallet.last_scanned_height = None
                    wallet.last_scan_at = None
                    wallet.scan_error = None
                giveaway.winning_transaction_id = None
                giveaway.winning_block_hash = None
                giveaway.winning_block_height = None
                logger.info(
                    "giveaway_deposit_address_changed",
                    giveaway_id=str(giveaway.id),
                )
            giveaway.deposit_address = body.deposit_address

    await db.commit()
    await db.refresh(giveaway)
    stats = await _compute_stats(db, giveaway)
    winner = await _compute_winner(db, giveaway)
    if winner is not None:
        winner = winner.model_copy(update={"eligible_count": stats.eligible_count})
    return _to_detail(giveaway, stats, winner)


@router.delete("/giveaways/{giveaway_id}", status_code=204)
async def delete_giveaway(
    giveaway_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> None:
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    giveaway = res.scalar_one_or_none()
    if not giveaway:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    # Explicit to avoid the circular winning_transaction_id reference.
    await db.execute(
        delete(Transaction).where(Transaction.giveaway_id == giveaway_id)
    )
    await db.delete(giveaway)
    await db.commit()
    logger.info("giveaway_deleted", giveaway_id=str(giveaway_id))


@router.post(
    "/giveaways/{giveaway_id}/pick-winner",
    response_model=GiveawayDetailResponse,
)
async def pick_winner(
    giveaway_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> GiveawayDetailResponse:
    """Run the provably-fair winner selection and close the giveaway."""
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    giveaway = res.scalar_one_or_none()
    if not giveaway:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    if giveaway.is_closed:
        raise HTTPException(status_code=409, detail="Giveaway is already closed.")

    now = datetime.now(timezone.utc)
    if now < giveaway.end_date:
        raise HTTPException(
            status_code=409,
            detail="Giveaway end date has not passed yet.",
        )

    daemon = DaemonRPCClient()
    try:
        result = await select_winner(giveaway, db, daemon=daemon)
    except WinnerSelectionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(
            "giveaway_pick_winner_failed", giveaway_id=str(giveaway.id), error=str(e)
        )
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach the Monero daemon to read the seed block: {e}",
        )
    finally:
        await daemon.close()

    giveaway.winning_transaction_id = (
        result.winning_transaction.id if result.winning_transaction else None
    )
    giveaway.winning_block_hash = result.block_header.hash
    giveaway.winning_block_height = result.block_header.height
    giveaway.is_closed = True
    await db.commit()
    await db.refresh(giveaway)

    logger.info(
        "giveaway_closed",
        giveaway_id=str(giveaway.id),
        has_winner=result.winning_transaction is not None,
        seed_height=result.block_header.height,
    )

    stats = await _compute_stats(db, giveaway)
    winner = await _compute_winner(db, giveaway)
    if winner is not None:
        winner = winner.model_copy(update={"eligible_count": result.eligible_count})
    return _to_detail(giveaway, stats, winner)


@router.get("/giveaways/{giveaway_id}/widget-png")
async def download_giveaway_widget_png(
    giveaway_id: uuid.UUID,
    format: str = Query("wide"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> Response:
    if format not in FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Choose from: {', '.join(FORMATS.keys())}",
        )
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    giveaway = res.scalar_one_or_none()
    if not giveaway:
        raise HTTPException(status_code=404, detail="Giveaway not found")

    total_res = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount_xmr), 0)).where(
            Transaction.giveaway_id == giveaway.id
        )
    )
    total_xmr = total_res.scalar()

    base_color = giveaway.widget_background_color or "#667eea"
    text_color = giveaway.widget_text_color or "#ffffff"

    png_bytes = generate_widget_png(
        label=giveaway.title,
        description=giveaway.description,
        public_website=giveaway.public_website,
        deposit_address=giveaway.deposit_address,
        target_amount_xmr=None,
        total_received_xmr=f"{total_xmr:.4f}",
        base_color=base_color,
        text_color=text_color,
        format_type=cast(WidgetFormat, format),
    )
    filename = f"{giveaway.title.replace(' ', '_')}_{format}.png"
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/giveaways/{giveaway_id}/static-widget")
async def get_giveaway_static_widget(
    giveaway_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Return the QR code data URL for the static giveaway widget."""
    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    giveaway = res.scalar_one_or_none()
    if not giveaway:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    qr_data_url = _generate_qr_data_url(giveaway.deposit_address, size=200)
    return {"qr_data_url": qr_data_url}


# NOTE: transaction listing for a giveaway is served by the shared
# transactions endpoint: GET /api/v1/giveaways/{id}/txs  (see below).


@router.get("/giveaways/{giveaway_id}/txs")
async def list_giveaway_transactions(
    giveaway_id: uuid.UUID,
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    tiers: str | None = Query(None),
    sort: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """List transactions recorded for a giveaway with pagination/sorting.

    Reuses the funds txs implementation by delegating to the shared helpers.
    """
    from app.api.v1.endpoints.transactions import _list_entity_transactions

    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    giveaway = res.scalar_one_or_none()
    if not giveaway:
        raise HTTPException(status_code=404, detail="Giveaway not found")

    return await _list_entity_transactions(
        db=db,
        entity_filter=Transaction.giveaway_id == giveaway_id,
        cursor=cursor,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        tiers=tiers,
        sort=sort,
    )


GIVEAWAY_EXPORT_FORMATS = {"pdf", "xlsx", "csv", "xml", "json"}


@router.get("/giveaways/{giveaway_id}/export/{export_format}")
async def export_giveaway_transactions(
    giveaway_id: uuid.UUID,
    export_format: str,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    tiers: str | None = Query(None),
    sort: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> Response:
    """Export a giveaway's transactions in the specified format."""
    if export_format not in GIVEAWAY_EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format: {export_format}. "
            f"Use {', '.join(sorted(GIVEAWAY_EXPORT_FORMATS))}.",
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be less than or equal to end_date",
        )

    tier_list: list[str] = []
    if tiers:
        tier_list = [t.strip().lower() for t in tiers.split(",") if t.strip()]
        invalid = [t for t in tier_list if t not in VALID_TIER_NAMES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier names: {', '.join(invalid)}. "
                f"Valid: micro, medium, large, whale",
            )

    sort_rules = parse_sort(sort)

    res = await db.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
    giveaway = res.scalar_one_or_none()
    if not giveaway:
        raise HTTPException(status_code=404, detail="Giveaway not found")

    # Build filtered query (no pagination)
    query = select(Transaction).where(Transaction.giveaway_id == giveaway_id)
    date_filter = build_date_filter(start_date, end_date)
    if date_filter is not None:
        query = query.where(date_filter)
    tier_filter = build_tier_filter(tier_list)
    if tier_filter is not None:
        query = query.where(tier_filter)
    for clause in build_order_by(sort_rules):
        query = query.order_by(clause)
    result = await db.execute(query)
    transactions = result.scalars().all()

    # Overall stats
    stats_result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_xmr), 0).label("total"),
            func.count(Transaction.id).label("count"),
        ).where(Transaction.giveaway_id == giveaway_id)
    )
    stats_row = stats_result.one()
    overall_total_xmr = str(stats_row.total)

    grand_total = str(sum(tx.amount_xmr for tx in transactions))

    filter_meta = describe_filters(start_date, end_date, tier_list, sort_rules)
    if not filter_meta.get("date_range"):
        filter_meta.pop("date_range", None)
    if not filter_meta.get("tiers"):
        filter_meta.pop("tiers", None)
    if not filter_meta.get("sort"):
        filter_meta.pop("sort", None)

    tx_dicts = [
        {
            "txid": tx.txid,
            "amount_atomic": tx.amount_atomic,
            "amount_xmr": str(tx.amount_xmr),
            "confirmations": tx.confirmations,
            "timestamp": tx.timestamp,
            "height": tx.height,
            "unlock_time": tx.unlock_time,
        }
        for tx in transactions
    ]

    dt_format = get_datetime_format()
    gid = str(giveaway_id)
    deposit_addr = giveaway.deposit_address

    # Giveaway-specific metadata included in JSON/XML exports
    extra = {
        "entity_type": "giveaway",
        "min_amount_xmr": str(giveaway.min_amount_xmr),
        "start_date": giveaway.start_date.isoformat(),
        "end_date": giveaway.end_date.isoformat(),
        "is_closed": giveaway.is_closed,
        "eligible_count": stats_row._mapping["count"],
    }
    if giveaway.winning_block_hash:
        extra["winning_block_height"] = giveaway.winning_block_height
        extra["winning_block_hash"] = giveaway.winning_block_hash
    if giveaway.is_closed:
        extra["status"] = "closed"
    elif datetime.now(timezone.utc) < giveaway.start_date:
        extra["status"] = "scheduled"
    elif datetime.now(timezone.utc) < giveaway.end_date:
        extra["status"] = "active"
    else:
        extra["status"] = "ended"

    if export_format == "pdf":
        data = generate_pdf_report(
            fund_label=giveaway.title,
            fund_description=giveaway.description,
            deposit_address=deposit_addr,
            wallet_height=None,
            transactions=tx_dicts,
            total_xmr=overall_total_xmr,
            target_xmr=None,
            grand_total=grand_total,
            date_from=start_date,
            date_to=end_date,
            datetime_format=dt_format,
            filter_metadata=filter_meta if filter_meta else None,
        )
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=giveaway_{gid}.pdf"},
        )

    if export_format == "xlsx":
        data = generate_xlsx_export(
            transactions=tx_dicts,
            fund_label=giveaway.title,
            datetime_format=dt_format,
        )
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=giveaway_{gid}.xlsx"
            },
        )

    if export_format == "csv":
        data = generate_csv_export(
            transactions=tx_dicts,
            fund_label=giveaway.title,
            datetime_format=dt_format,
        )
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=giveaway_{gid}.csv"},
        )

    if export_format == "xml":
        data = generate_xml_report(
            fund_label=giveaway.title,
            transactions=tx_dicts,
            total_xmr=overall_total_xmr,
            datetime_format=dt_format,
            fund_description=giveaway.description,
            fund_id=gid,
            deposit_address=deposit_addr,
            filter_metadata=filter_meta if filter_meta else None,
            extra_metadata=extra,
        )
        return Response(
            content=data,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename=giveaway_{gid}.xml"},
        )

    # json
    data = generate_json_export(
        transactions=tx_dicts,
        fund_label=giveaway.title,
        fund_id=gid,
        datetime_format=dt_format,
        filter_metadata=filter_meta if filter_meta else None,
        extra_metadata=extra,
    )
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=giveaway_{gid}.json"},
    )
