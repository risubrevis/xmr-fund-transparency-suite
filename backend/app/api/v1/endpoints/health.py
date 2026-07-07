import os
import time

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Wallet

router = APIRouter()


async def check_db_latency(db: AsyncSession) -> dict:
    """Check database connection and latency."""
    start = time.time()
    try:
        await db.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def check_redis_latency() -> dict:
    """Check Redis connection and latency."""
    start = time.time()
    try:
        import redis.asyncio as aioredis

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        r = aioredis.from_url(redis_url)
        await r.ping()
        await r.aclose()
        latency_ms = round((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def check_rpc_status(rpc_url: str) -> dict:
    """Check Monero RPC connection and sync status."""
    start = time.time()
    try:
        rpc_base_url = rpc_url.replace("/json_rpc", "").rstrip("/")
        async with httpx.AsyncClient(timeout=5.0) as client:
            daemon_response = await client.post(
                f"{rpc_base_url}/json_rpc",
                json={"jsonrpc": "2.0", "id": "0", "method": "get_info"},
            )
            daemon_response.raise_for_status()
            daemon_data = daemon_response.json()
            daemon_height = daemon_data.get("result", {}).get("height", 0)

            wallet_response = await client.post(
                f"{rpc_base_url}/json_rpc",
                json={"jsonrpc": "2.0", "id": "0", "method": "get_height"},
            )
            wallet_response.raise_for_status()
            wallet_data = wallet_response.json()
            wallet_height = wallet_data.get("result", {}).get("height", 0)

        latency_ms = round((time.time() - start) * 1000)
        sync_progress = (
            round((wallet_height / daemon_height) * 100, 1) if daemon_height > 0 else 0
        )

        return {
            "status": "ok",
            "latency_ms": latency_ms,
            "daemon_height": daemon_height,
            "wallet_height": wallet_height,
            "sync_progress": sync_progress,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/health")
async def healthcheck(db: AsyncSession = Depends(get_db)) -> dict:
    """Comprehensive health check endpoint."""
    db_status = await check_db_latency(db)
    redis_status = await check_redis_latency()
    rpc_url = os.environ.get("MONERO_RPC_URL", "http://localhost:18082/json_rpc")
    rpc_status = await check_rpc_status(rpc_url)

    # Get scanner status from all active wallets
    result = await db.execute(select(Wallet).where(Wallet.is_active.is_(True)))
    active_wallets = result.scalars().all()

    wallets_status = []
    for wallet in active_wallets:
        wallets_status.append(
            {
                "wallet_id": str(wallet.id),
                "name": wallet.name,
                "last_scan_at": (
                    wallet.last_scan_at.isoformat() if wallet.last_scan_at else None
                ),
                "last_scanned_height": wallet.last_scanned_height,
                "scan_error": wallet.scan_error,
            }
        )

    scanner_status = {
        "active_wallet_count": len(active_wallets),
        "wallets": wallets_status,
    }

    all_statuses = [db_status["status"], redis_status["status"], rpc_status["status"]]
    if all(s == "ok" for s in all_statuses):
        overall_status = "ok"
    elif any(s == "ok" for s in all_statuses):
        overall_status = "degraded"
    else:
        overall_status = "down"

    return {
        "status": overall_status,
        "components": {
            "db": db_status,
            "redis": redis_status,
            "rpc": rpc_status,
        },
        "scanner": scanner_status,
    }
