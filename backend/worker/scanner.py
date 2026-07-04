import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import httpx
from app.config import settings
from app.crypto import ViewKeyEncryption
from app.database import async_session_factory
from app.logging import get_logger
from app.models import Fund, Transaction, Wallet
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("worker.scanner")

ATOMIC_PER_XMR = Decimal("1e12")
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2


class MoneroScanner:
    """
    Async scanner for view-only wallets.

    Scans all active wallets and records incoming transactions
    for each fund's deposit_address. Uses incremental scanning
    via last_scanned_height on the Wallet model.

    In multi-wallet mode, each wallet is opened by its deterministic
    filename (wallet_{uuid}) before querying transfers.
    """

    def __init__(self, rpc_url: str, scan_interval: int = 60):
        self.rpc_url = rpc_url.replace("/json_rpc", "").rstrip("/")
        self.scan_interval = scan_interval
        self._http_client: Optional[httpx.AsyncClient] = None
        self._cipher: Optional[ViewKeyEncryption] = None

    def _get_cipher(self) -> ViewKeyEncryption:
        """Lazily initialize the view key cipher."""
        if self._cipher is None:
            self._cipher = ViewKeyEncryption(settings.view_key_master_secret)
        return self._cipher

    def _wallet_filename(self, wallet: Wallet) -> str:
        """Deterministic RPC filename for a wallet based on its UUID."""
        return f"wallet_{wallet.uuid}"

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=120.0)
        return self._http_client

    async def _rpc_call(
        self, method: str, params: dict = None, timeout: float | None = None
    ) -> dict:
        """JSON-RPC call with retry and exponential backoff."""
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": method,
            "params": params or {},
        }
        client = await self._get_http_client()
        request_timeout = timeout or client.timeout.read
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = await client.post(
                    f"{self.rpc_url}/json_rpc", json=payload, timeout=request_timeout
                )
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

    async def _ensure_wallet_open(self, filename: str) -> bool:
        """Open a wallet on monero-wallet-rpc by filename.

        Returns True if the wallet is available (opened or already open).
        Returns False if the wallet file was not found on the RPC.
        Handles the "already open" case gracefully. After opening,
        waits briefly for the wallet to start syncing with the daemon.
        """
        try:
            result = await self._rpc_call(
                "open_wallet", {"filename": filename, "password": ""}
            )
            logger.info(
                "wallet_opened",
                filename=filename,
                result=str(result)[:100] if result else "empty",
            )
            await asyncio.sleep(3)
            return True
        except RuntimeError as e:
            err_msg = str(e).lower()
            if "already open" in err_msg or "wallet already" in err_msg:
                logger.info("wallet_already_open", filename=filename)
                return True
            logger.warning("open_wallet_failed", filename=filename, error=str(e))
            return False

    async def _register_wallet_if_needed(self, wallet: Wallet, filename: str) -> bool:
        """Re-register a wallet on monero-wallet-rpc if it is not found.

        This handles the case where the RPC container was restarted and
        wallet files need to be recreated from keys. Returns True if
        the wallet was (re-)registered, False if it was already available.
        """
        try:
            await self._rpc_call("open_wallet", {"filename": filename, "password": ""})
            # Wallet opened successfully — it's already registered
            return False
        except RuntimeError as e:
            if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
                logger.info(
                    "wallet_not_found_re_registering",
                    wallet_id=str(wallet.id),
                    filename=filename,
                )
                cipher = self._get_cipher()
                decrypted_view_key = cipher.decrypt(wallet.view_key)
                try:
                    await self._rpc_call(
                        "generate_from_keys",
                        {
                            "filename": filename,
                            "address": wallet.primary_address,
                            "viewkey": decrypted_view_key,
                            "restore_height": wallet.start_height,
                            "password": "",
                        },
                        timeout=300.0,
                    )
                    logger.info(
                        "wallet_re_registered",
                        wallet_id=str(wallet.id),
                        filename=filename,
                    )
                    return True
                except RuntimeError as regen_err:
                    if (
                        "file_exists" in str(regen_err).lower()
                        or "already exists" in str(regen_err).lower()
                    ):
                        logger.info(
                            "wallet_file_exists_opening",
                            wallet_id=str(wallet.id),
                            filename=filename,
                        )
                        await self._rpc_call(
                            "open_wallet",
                            {"filename": filename, "password": ""},
                        )
                        return True
                    raise
            # "already open" is fine — wallet is available
            if "already open" in str(e).lower():
                return False
            raise

    async def sync_wallet(
        self, wallet: Wallet, funds: list[Fund], db: AsyncSession
    ) -> int:
        """
        Sync a wallet and record incoming transactions for each fund.

        Only records transactions whose destination address matches
        a fund's deposit_address.
        """
        filename = self._wallet_filename(wallet)
        from_height = wallet.last_scanned_height or wallet.start_height

        # Build a lookup: deposit_address -> fund
        fund_by_address: dict[str, Fund] = {}
        for fund in funds:
            fund_by_address[fund.deposit_address] = fund

        result = await self._rpc_call(
            "get_transfers",
            {
                "filename": filename,
                "in": True,
                "account_index": 0,
                "filter_by_height": True,
                "min_height": from_height,
            },
        )

        incoming = result.get("in", [])
        new_count = 0
        skipped_count = 0

        for tx in incoming:
            # Filter: only record transactions sent to a known deposit address
            tx_address = tx.get("address", "")
            fund = fund_by_address.get(tx_address)

            if fund is None:
                skipped_count += 1
                logger.debug(
                    "skipping_tx_address_mismatch",
                    txid=tx["txid"],
                    tx_address=tx_address[:12] + "...",
                    known_addresses=list(fund_by_address.keys()),
                )
                continue

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
                wallet_id=wallet.id,
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

        # Update scan metadata — advance height based on ALL incoming transfers,
        # not just filtered ones, so we don't re-process skipped blocks
        wallet.last_scanned_height = max(
            (tx.get("height", 0) for tx in incoming),
            default=from_height,
        )
        wallet.last_scan_at = datetime.now(tz=timezone.utc)
        wallet.scan_error = None  # Clear error on success

        await db.commit()
        logger.info(
            "scan_complete",
            wallet_id=str(wallet.id),
            filename=filename,
            new_tx_count=new_count,
            skipped_count=skipped_count,
            last_scanned_height=wallet.last_scanned_height,
        )

        return new_count

    async def run_loop(self) -> None:
        """Infinite scanning loop for all active wallets."""
        logger.info("scanner_started", interval=self.scan_interval)

        while True:
            try:
                async with async_session_factory() as db:
                    # Acquire advisory lock to prevent parallel workers
                    await db.execute(text("SELECT pg_advisory_lock(12345)"))

                    try:
                        # Get all active wallets
                        result = await db.execute(
                            select(Wallet).where(Wallet.is_active.is_(True))
                        )
                        wallets = result.scalars().all()

                        if not wallets:
                            logger.warning("no_active_wallets")
                        else:
                            for wallet in wallets:
                                filename = self._wallet_filename(wallet)
                                try:
                                    # Ensure wallet is loaded in RPC memory.
                                    # If not found (e.g. RPC container restarted),
                                    # re-register it from the stored encrypted view key.
                                    opened = await self._ensure_wallet_open(filename)
                                    if not opened:
                                        registered = (
                                            await self._register_wallet_if_needed(
                                                wallet, filename
                                            )
                                        )
                                        if not registered:
                                            wallet.scan_error = (
                                                "Wallet not found on RPC and "
                                                "could not be re-registered"
                                            )
                                            await db.commit()
                                            logger.error(
                                                "wallet_unavailable",
                                                wallet_id=str(wallet.id),
                                                filename=filename,
                                            )
                                            continue

                                    # Get all active funds for this wallet
                                    funds_result = await db.execute(
                                        select(Fund).where(
                                            Fund.wallet_id == wallet.id,
                                            Fund.is_active.is_(True),
                                        )
                                    )
                                    funds = funds_result.scalars().all()

                                    if not funds:
                                        logger.info(
                                            "no_active_funds_for_wallet",
                                            wallet_id=str(wallet.id),
                                            filename=filename,
                                        )
                                        # Still update scan height even with no funds
                                        try:
                                            await self._rpc_call(
                                                "get_height",
                                                {"filename": filename},
                                            )
                                        except Exception:
                                            pass  # Non-critical
                                        wallet.last_scan_at = datetime.now(
                                            tz=timezone.utc
                                        )
                                        await db.commit()
                                        continue

                                    await self.sync_wallet(wallet, list(funds), db)
                                except Exception as e:
                                    wallet.scan_error = str(e)[:500]
                                    await db.commit()
                                    logger.error(
                                        "sync_failed",
                                        wallet_id=str(wallet.id),
                                        filename=filename,
                                        error=str(e),
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
