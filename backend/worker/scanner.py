import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import httpx
from app.config import settings
from app.database import async_session_factory
from app.logging import get_logger
from app.models import Fund, Transaction
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("worker.scanner")

ATOMIC_PER_XMR = Decimal("1e12")
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2


class MoneroScanner:
    """
    Async scanner for a SINGLE view-only wallet.
    One application instance = one wallet = one fund.

    Uses last_scanned_height for incremental scanning and
    txid-based deduplication for idempotent processing.
    """

    def __init__(self, rpc_url: str, scan_interval: int = 60):
        self.rpc_url = rpc_url.replace("/json_rpc", "").rstrip("/")
        self.scan_interval = scan_interval
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=120.0)
        return self._http_client

    async def _rpc_call(self, method: str, params: dict = None) -> dict:
        """JSON-RPC call with retry and exponential backoff."""
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": method,
            "params": params or {},
        }
        client = await self._get_http_client()
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = await client.post(f"{self.rpc_url}/json_rpc", json=payload)
                r.raise_for_status()
                data = r.json()
                if "error" in data:
                    raise RuntimeError(
                        f"RPC error: {data['error'].get('message', data['error'])}"
                    )
                return data["result"]
            except (httpx.HTTPStatusError, httpx.ConnectError) as e:
                last_error = e
                wait = RETRY_BACKOFF_BASE**attempt
                logger.warning(
                    "rpc_call_failed",
                    method=method,
                    attempt=attempt,
                    max_retries=MAX_RETRIES,
                    retry_in=wait,
                    error=str(e),
                )
                await asyncio.sleep(wait)

        raise RuntimeError(
            f"RPC call '{method}' failed after {MAX_RETRIES} attempts: {last_error}"
        )

    async def _ensure_wallet_open(self) -> None:
        """Open the view-only wallet before scanning.
        
        Always attempts to open the wallet. If already open, monero-wallet-rpc
        silently succeeds. After opening, waits briefly for wallet to sync.
        """
        try:
            result = await self._rpc_call("open_wallet", {"filename": "viewonly", "password": ""})
            logger.info("wallet_opened", result=str(result)[:100] if result else "empty")
            # Give the wallet time to start syncing with the daemon
            await asyncio.sleep(5)
        except Exception as e:
            err_msg = str(e).lower()
            if "already open" in err_msg or "wallet already" in err_msg:
                logger.info("wallet_already_open")
            else:
                logger.warning("open_wallet_failed", error=str(e))

    async def sync_fund(self, fund: Fund, db: AsyncSession) -> int:
        """
        Sync the single fund.
        Returns the number of new transactions found.
        """
        from_height = fund.last_scanned_height or fund.start_height

        result = await self._rpc_call(
            "get_transfers",
            {
                "in": True,
                "account_index": 0,
                "filter_by_height": True,
                "min_height": from_height,
            },
        )

        incoming = result.get("in", [])
        new_count = 0

        for tx in incoming:
            exists = await db.execute(
                select(Transaction).where(
                    Transaction.txid == tx["txid"], Transaction.fund_id == fund.id
                )
            )
            if exists.scalar_one_or_none():
                continue

            amount_xmr = Decimal(str(tx["amount"])) / ATOMIC_PER_XMR
            new_tx = Transaction(
                fund_id=fund.id,
                txid=tx["txid"],
                amount_atomic=tx["amount"],
                amount_xmr=amount_xmr,
                confirmations=tx.get("confirmations", 0),
                timestamp=datetime.fromtimestamp(tx["timestamp"], tz=timezone.utc),
                unlock_time=tx.get("unlock_time"),
                height=tx.get("height", 0),
            )
            db.add(new_tx)
            new_count += 1

        # Update scan metadata
        fund.last_scanned_height = max(
            (tx.get("height", 0) for tx in incoming),
            default=from_height,
        )
        fund.last_scan_at = datetime.now(tz=timezone.utc)
        fund.scan_error = None  # Clear error on success

        await db.commit()
        logger.info(
            "scan_complete",
            fund_id=str(fund.id),
            new_tx_count=new_count,
            last_scanned_height=fund.last_scanned_height,
        )

        return new_count

    async def run_loop(self) -> None:
        """Infinite scanning loop for the single fund."""
        logger.info("scanner_started", interval=self.scan_interval)

        while True:
            try:
                async with async_session_factory() as db:
                    # Acquire advisory lock to prevent parallel workers
                    await db.execute(text("SELECT pg_advisory_lock(12345)"))

                    try:
                        result = await db.execute(
                            select(Fund).where(Fund.is_active.is_(True))
                        )
                        fund = result.scalar_one_or_none()

                        if fund is None:
                            logger.warning("no_active_fund")
                        else:
                            # Ensure wallet is open before scanning
                            await self._ensure_wallet_open()
                            try:
                                await self.sync_fund(fund, db)
                            except Exception as e:
                                fund.scan_error = str(e)[:500]
                                await db.commit()
                                logger.error(
                                    "sync_failed", fund_id=str(fund.id), error=str(e)
                                )
                    finally:
                        await db.execute(text("SELECT pg_advisory_unlock(12345)"))
                        await db.commit()
            except Exception as e:
                logger.error("scanner_loop_error", error=str(e))

            await asyncio.sleep(self.scan_interval)

    async def shutdown(self) -> None:
        """Clean up resources."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        logger.info("scanner_shutdown")


async def main() -> None:
    """Entry point for the worker process."""
    from app.logging import setup_logging

    setup_logging(settings.log_level, settings.log_format)

    scanner = MoneroScanner(
        rpc_url=settings.monero_rpc_url,
        scan_interval=settings.scan_interval,
    )

    try:
        await scanner.run_loop()
    except asyncio.CancelledError:
        await scanner.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
