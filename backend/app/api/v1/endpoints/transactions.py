import base64
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.filters import (
    VALID_TIER_NAMES,
    SortRule,
    build_date_filter,
    build_order_by,
    build_tier_filter,
    parse_sort,
)
from app.models import Fund, Transaction
from app.schemas import TransactionListResponse, TransactionResponse

router = APIRouter()


@router.get("/funds/{fund_id}/txs", response_model=TransactionListResponse)
async def list_transactions(
    fund_id: uuid.UUID,
    cursor: str | None = Query(
        None, description="Base64-encoded cursor for pagination"
    ),
    limit: int = Query(20, ge=1, le=100),
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
) -> TransactionListResponse:
    """List transactions for a fund with optional filtering, sorting, and cursor-based pagination."""
    # Validate start_date <= end_date
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be less than or equal to end_date",
        )

    # Parse tier names
    tier_list: list[str] = []
    if tiers:
        tier_list = [t.strip().lower() for t in tiers.split(",") if t.strip()]
        invalid = [t for t in tier_list if t not in VALID_TIER_NAMES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier names: {', '.join(invalid)}. Valid: micro, medium, large, whale",
            )

    # Parse sort rules
    sort_rules: list[SortRule] = parse_sort(sort)

    # Verify fund exists
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Build base query
    query = select(Transaction).where(Transaction.fund_id == fund_id)

    # Apply date range filter
    date_filter = build_date_filter(start_date, end_date)
    if date_filter is not None:
        query = query.where(date_filter)

    # Apply tier filter
    tier_filter = build_tier_filter(tier_list)
    if tier_filter is not None:
        query = query.where(tier_filter)

    # Apply ordering
    order_clauses = build_order_by(sort_rules)
    for clause in order_clauses:
        query = query.order_by(clause)

    # Decode cursor for pagination
    if cursor:
        try:
            cursor_id = uuid.UUID(bytes=base64.urlsafe_b64decode(cursor))
            cursor_tx = await db.execute(
                select(Transaction).where(Transaction.id == cursor_id)
            )
            cursor_tx_obj = cursor_tx.scalar_one_or_none()
            if cursor_tx_obj:
                # Use the ordering to determine the cursor boundary
                # For simplicity, fall back to height-based cursor
                query = query.where(Transaction.height < cursor_tx_obj.height)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    query = query.limit(limit + 1)
    result = await db.execute(query)
    txs = result.scalars().all()

    has_more = len(txs) > limit
    items = txs[:limit]

    next_cursor = None
    if has_more and items:
        next_cursor = base64.urlsafe_b64encode(items[-1].id.bytes).decode()

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(tx) for tx in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )
