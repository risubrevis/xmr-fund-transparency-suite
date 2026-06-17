import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.models import Fund

router = APIRouter()


async def event_generator(fund_id: uuid.UUID, api_key: str):
    """SSE event generator for fund updates."""
    from app.database import async_session_factory

    async with async_session_factory() as db:
        result = await db.execute(select(Fund).where(Fund.id == fund_id))
        fund = result.scalar_one_or_none()
        if not fund:
            yield f"data: {json.dumps({'error': 'Fund not found'})}\n\n"
            return

        try:
            while True:
                await db.refresh(fund)
                status = {
                    "type": "status",
                    "last_scanned_height": fund.last_scanned_height,
                    "last_scan_at": fund.last_scan_at.isoformat()
                    if fund.last_scan_at
                    else None,
                    "scan_error": fund.scan_error,
                }
                yield f"event: status\ndata: {json.dumps(status)}\n\n"
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass


@router.get("/funds/{fund_id}/events")
async def fund_events(
    fund_id: uuid.UUID,
    api_key: str = Depends(verify_api_key),
):
    """Server-Sent Events stream for fund updates."""
    return StreamingResponse(
        event_generator(fund_id, api_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
