import base64
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
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
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
) -> TransactionListResponse:
    """List transactions for a fund with cursor-based pagination."""
    # Verify fund exists
    result = await db.execute(select(Fund).where(Fund.id == fund_id))
    fund = result.scalar_one_or_none()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Build query
    query = (
        select(Transaction)
        .where(Transaction.fund_id == fund_id)
        .order_by(Transaction.height.desc(), Transaction.timestamp.desc())
    )

    # Decode cursor (cursor is base64-encoded transaction id)
    if cursor:
        try:
            cursor_id = uuid.UUID(bytes=base64.urlsafe_b64decode(cursor))
            # Get the cursor transaction to find the height/timestamp boundary
            cursor_tx = await db.execute(
                select(Transaction).where(Transaction.id == cursor_id)
            )
            cursor_tx_obj = cursor_tx.scalar_one_or_none()
            if cursor_tx_obj:
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
