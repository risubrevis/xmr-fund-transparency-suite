"""Unified export endpoint for all file formats (PDF, XLSX, CSV, XML, JSON).

All formats share the same filter/sort logic and apply the exact same WHERE/ORDER BY
clauses as the paginated transaction list, but without pagination limits.
"""

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.filters import (
    VALID_TIER_NAMES,
    SortRule,
    build_date_filter,
    build_order_by,
    build_tier_filter,
    describe_filters,
    parse_sort,
)
from app.logging import get_logger
from app.models import Fund, Transaction
from app.reports.csv_export import generate_csv_export
from app.reports.json_export import generate_json_export
from app.reports.pdf import generate_pdf_report
from app.reports.xlsx import generate_xlsx_export
from app.reports.xml import generate_xml_report
from app.settings import get_datetime_format

logger = get_logger("api.exports")
router = APIRouter()


async def _get_filtered_transactions(
    fund_id: uuid.UUID,
    start_date: datetime | None,
    end_date: datetime | None,
    tier_list: List[str],
    sort_rules: List[SortRule],
    db: AsyncSession,
) -> List[Transaction]:
    """Build and execute a filtered, sorted query (no pagination)."""
    query = select(Transaction).where(Transaction.fund_id == fund_id)

    date_filter = build_date_filter(start_date, end_date)
    if date_filter is not None:
        query = query.where(date_filter)

    tier_filter = build_tier_filter(tier_list)
    if tier_filter is not None:
        query = query.where(tier_filter)

    order_clauses = build_order_by(sort_rules)
    for clause in order_clauses:
        query = query.order_by(clause)

    result = await db.execute(query)
    return result.scalars().all()


def _tx_to_dict(tx: Transaction) -> dict:
    """Convert a Transaction ORM object to a dict for report generators."""
    return {
        "txid": tx.txid,
        "amount_atomic": tx.amount_atomic,
        "amount_xmr": str(tx.amount_xmr),
        "confirmations": tx.confirmations,
        "timestamp": tx.timestamp,
        "height": tx.height,
        "unlock_time": tx.unlock_time,
    }


@router.get("/funds/{fund_id}/export/{export_format}")
async def export_transactions(
    fund_id: uuid.UUID,
    export_format: str,
    start_date: datetime | None = Query(
        None, description="ISO timestamp: filter transactions from this date"
    ),
    end_date: datetime | None = Query(
        None, description="ISO timestamp: filter transactions up to this date"
    ),
    tiers: str | None = Query(
        None, description="Comma-separated tier names: micro,medium,large,whale"
    ),
    sort: str | None = Query(
        None,
        description="Multi-sort: comma-separated field:dir pairs, e.g. timestamp:desc,amount_xmr:asc",
    ),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> Response:
    """Export transactions in the specified format with optional filters and sorting."""
    if export_format not in ("pdf", "xlsx", "csv", "xml", "json"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format: {export_format}. Use pdf, xlsx, csv, xml, or json.",
        )

    # Validate dates
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be less than or equal to end_date",
        )

    # Parse tiers
    tier_list: List[str] = []
    if tiers:
        tier_list = [t.strip().lower() for t in tiers.split(",") if t.strip()]
        invalid = [t for t in tier_list if t not in VALID_TIER_NAMES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier names: {', '.join(invalid)}. Valid: micro, medium, large, whale",
            )

    # Parse sort
    sort_rules: List[SortRule] = parse_sort(sort)

    # Verify fund exists and get metadata
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Get filtered transactions (no pagination)
    transactions = await _get_filtered_transactions(
        fund_id, start_date, end_date, tier_list, sort_rules, db
    )

    # Compute totals
    total_xmr = sum(tx.amount_xmr for tx in transactions)
    grand_total = str(total_xmr)

    # Get overall stats (total across ALL transactions, not just filtered)
    stats_result = await db.execute(
        select(
            func.coalesce(func.sum(Transaction.amount_xmr), 0).label("total"),
            func.count(Transaction.id).label("count"),
        ).where(Transaction.fund_id == fund_id)
    )
    stats_row = stats_result.one()
    overall_total_xmr = str(stats_row.total)

    # Build filter metadata for reports
    filter_meta = describe_filters(start_date, end_date, tier_list, sort_rules)
    # Remove None entries
    if not filter_meta.get("date_range"):
        filter_meta.pop("date_range", None)
    if not filter_meta.get("tiers"):
        filter_meta.pop("tiers", None)
    if not filter_meta.get("sort"):
        filter_meta.pop("sort", None)

    # Convert transactions to dicts
    tx_dicts = [_tx_to_dict(tx) for tx in transactions]

    dt_format = get_datetime_format()

    # Use deposit_address from the fund
    deposit_addr = fund.deposit_address
    fund_id_str = str(fund_id)

    if export_format == "pdf":
        data = generate_pdf_report(
            fund_label=fund.label,
            fund_description=fund.description,
            deposit_address=deposit_addr,
            wallet_height=None,
            transactions=tx_dicts,
            total_xmr=overall_total_xmr,
            target_xmr=str(fund.target_amount_xmr) if fund.target_amount_xmr else None,
            grand_total=grand_total,
            date_from=start_date,
            date_to=end_date,
            datetime_format=dt_format,
            filter_metadata=filter_meta if filter_meta else None,
        )
        return Response(
            content=data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report_{fund_id_str}.pdf"
            },
        )

    elif export_format == "xlsx":
        data = generate_xlsx_export(
            transactions=tx_dicts,
            fund_label=fund.label,
            datetime_format=dt_format,
        )
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=export_{fund_id_str}.xlsx"
            },
        )

    elif export_format == "csv":
        data = generate_csv_export(
            transactions=tx_dicts,
            fund_label=fund.label,
            datetime_format=dt_format,
        )
        return Response(
            content=data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=export_{fund_id_str}.csv"
            },
        )

    elif export_format == "xml":
        data = generate_xml_report(
            fund_label=fund.label,
            transactions=tx_dicts,
            total_xmr=overall_total_xmr,
            datetime_format=dt_format,
            fund_description=fund.description,
            fund_id=fund_id_str,
            deposit_address=deposit_addr,
            filter_metadata=filter_meta if filter_meta else None,
        )
        return Response(
            content=data,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename=export_{fund_id_str}.xml"
            },
        )

    elif export_format == "json":
        data = generate_json_export(
            transactions=tx_dicts,
            fund_label=fund.label,
            fund_id=fund_id_str,
            datetime_format=dt_format,
            filter_metadata=filter_meta if filter_meta else None,
        )
        return Response(
            content=data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=export_{fund_id_str}.json"
            },
        )
