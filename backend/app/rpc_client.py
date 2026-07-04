"""Monero Wallet RPC client for multi-wallet operations.

Supports monero-wallet-rpc running with --wallet-dir, which allows
multiple wallets to be managed concurrently. Each wallet is identified
by a deterministic filename based on its database UUID:
wallet_{wallet_uuid}.
"""

from typing import Optional

import httpx

from app.config import settings
from app.logging import get_logger

logger = get_logger("app.rpc_client")

# Reuse httpx client across calls
_http_client: Optional[httpx.AsyncClient] = None


async def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=60.0)
    return _http_client


class WalletRPCError(Exception):
    """Raised when monero-wallet-rpc returns an error or is unreachable."""

    def __init__(self, message: str, rpc_code: int | None = None):
        self.rpc_code = rpc_code
        super().__init__(message)


async def rpc_call(
    method: str, params: dict = None, timeout: float | None = None
) -> dict:
    """Make a JSON-RPC call to monero-wallet-rpc.

    Raises WalletRPCError on any failure with a descriptive message.
    """
    client = await _get_client()
    request_timeout = timeout or client.timeout.read
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": method,
        "params": params or {},
    }

    try:
        r = await client.post(
            settings.monero_rpc_url, json=payload, timeout=request_timeout
        )
    except httpx.ConnectError as e:
        raise WalletRPCError(
            f"Cannot connect to monero-wallet-rpc at {settings.monero_rpc_url}. "
            f"Ensure the service is running."
        ) from e
    except httpx.TimeoutException as e:
        raise WalletRPCError(
            f"monero-wallet-rpc timed out after {request_timeout}s "
            f"while calling '{method}'. The wallet may be busy syncing — "
            f"try again in a moment."
        ) from e

    if r.status_code != 200:
        raise WalletRPCError(
            f"monero-wallet-rpc returned HTTP {r.status_code}. Response: {r.text[:500]}"
        )

    data = r.json()
    if "error" in data:
        err = data["error"]
        err_msg = err.get("message", str(err))
        err_code = err.get("code")
        logger.error(
            "rpc_error",
            method=method,
            error_code=err_code,
            error_message=err_msg,
        )
        raise WalletRPCError(
            f"monero-wallet-rpc error calling '{method}': {err_msg}",
            rpc_code=err_code,
        )

    return data["result"]


async def create_view_only_wallet(
    address: str,
    view_key: str,
    start_height: int,
    filename: str,
    password: str = "",
) -> dict:
    """Create a view-only wallet on monero-wallet-rpc using generate_from_keys.

    Uses the deterministic filename (wallet_{uuid}) to register the wallet
    in the multi-wallet RPC environment.

    If the wallet file already exists, closes the current wallet context
    and re-opens the existing one.

    Returns the RPC response dict.
    """
    logger.info(
        "creating_view_only_wallet",
        filename=filename,
        address=address[:12] + "...",
        start_height=start_height,
    )
    try:
        result = await rpc_call(
            "generate_from_keys",
            {
                "filename": filename,
                "address": address,
                "viewkey": view_key,
                "restore_height": start_height,
                "password": password,
            },
            timeout=300.0,  # 5 minutes for wallet creation/sync
        )
        logger.info(
            "view_only_wallet_created",
            filename=filename,
            result=str(result)[:200],
        )
        return result
    except WalletRPCError as e:
        # If wallet file already exists, close current context and re-open
        if "file_exists" in str(e).lower() or "already exists" in str(e).lower():
            logger.info(
                "wallet_file_exists_reopening",
                filename=filename,
                original_error=str(e),
            )
            try:
                await close_wallet()
            except Exception:
                pass  # No wallet may be open

            result = await open_wallet(filename, password)
            logger.info("wallet_reopened", filename=filename)
            return result
        raise


async def open_wallet(filename: str, password: str = "") -> dict:
    """Open an existing wallet on monero-wallet-rpc by filename.

    Handles the "already open" error (RPC code -7) gracefully —
    if the wallet is already loaded in memory, just proceed.
    """
    logger.info("opening_wallet", filename=filename)
    try:
        return await rpc_call(
            "open_wallet",
            {"filename": filename, "password": password},
        )
    except WalletRPCError as e:
        if e.rpc_code == -7 or "already open" in str(e).lower():
            # Wallet is already open in memory — this is fine
            logger.info("wallet_already_open", filename=filename)
            return {}
        raise


async def get_transfers(
    filename: str,
    min_height: int,
    account_index: int = 0,
) -> dict:
    """Get incoming transfers for a specific wallet.

    The filename parameter routes the request to the correct wallet
    in multi-wallet mode.
    """
    return await rpc_call(
        "get_transfers",
        {
            "filename": filename,
            "in": True,
            "account_index": account_index,
            "filter_by_height": True,
            "min_height": min_height,
        },
    )


async def get_wallet_height(filename: str) -> int:
    """Get the current block height for a specific wallet."""
    result = await rpc_call("get_height", {"filename": filename})
    return result.get("height", 0)


async def get_balance(filename: str, account_index: int = 0) -> dict:
    """Get the balance for a specific wallet."""
    return await rpc_call(
        "get_balance",
        {"filename": filename, "account_index": account_index},
    )


async def close_wallet(filename: str | None = None) -> None:
    """Close a wallet on monero-wallet-rpc.

    In multi-wallet mode, if filename is provided, the wallet with
    that filename is closed. If filename is None, the currently
    active wallet context is closed.
    """
    params = {}
    if filename:
        params["filename"] = filename
    try:
        await rpc_call("close_wallet", params)
    except Exception:
        pass  # Ignore errors if no wallet is open
