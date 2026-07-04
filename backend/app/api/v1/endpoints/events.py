import asyncio
import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.auth import verify_api_key
from app.models import Wallet

router = APIRouter()


async def event_generator(wallet_id: uuid.UUID, api_key: str):
    """SSE event generator for wallet scan updates."""
    from app.database import async_session_factory

    async with async_session_factory() as db:
        result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
        wallet = result.scalar_one_or_none()
        if not wallet:
            yield f"data: {json.dumps({'error': 'Wallet not found'})}\n\n"
            return

        try:
            while True:
                await db.refresh(wallet)
                status = {
                    "type": "status",
                    "last_scanned_height": wallet.last_scanned_height,
                    "last_scan_at": wallet.last_scan_at.isoformat()
                    if wallet.last_scan_at
                    else None,
                    "scan_error": wallet.scan_error,
                }
                yield f"event: status\ndata: {json.dumps(status)}\n\n"
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass


@router.get("/wallets/{wallet_id}/events")
async def wallet_events(
    wallet_id: uuid.UUID,
    api_key: str = Depends(verify_api_key),
):
    """Server-Sent Events stream for wallet scan updates."""
    return StreamingResponse(
        event_generator(wallet_id, api_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
