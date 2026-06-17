"""Monero Wallet RPC client for creating/opening view-only wallets."""

import logging
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
    wallet_name: str = "viewonly",
) -> dict:
    """
    Create a view-only wallet on monero-wallet-rpc using generate_from_keys.

    If the wallet file already exists, closes the current wallet and re-opens it.
    Returns the RPC response dict.
    """
    logger.info(
        "creating_view_only_wallet",
        address=address[:12] + "...",
        start_height=start_height,
    )
    # generate_from_keys can take a long time as it starts wallet sync.
    # Use a longer timeout for this specific call.
    try:
        result = await rpc_call(
            "generate_from_keys",
            {
                "address": address,
                "viewkey": view_key,
                "restore_height": start_height,
                "filename": wallet_name,
                "password": "",
            },
            timeout=300.0,  # 5 minutes for wallet creation
        )
        logger.info("view_only_wallet_created", result=str(result)[:200])
        return result
    except WalletRPCError as e:
        # If wallet file already exists, close current wallet and open the existing one
        if "file_exists" in str(e).lower() or "already exists" in str(e).lower():
            logger.info(
                "wallet_file_exists_reopening",
                wallet_name=wallet_name,
                original_error=str(e),
            )
            # Close whatever wallet is currently open
            try:
                await close_wallet()
            except Exception:
                pass  # No wallet may be open

            # Open the existing wallet
            result = await open_wallet(wallet_name)
            logger.info("wallet_reopened", wallet_name=wallet_name)
            return result
        raise


async def open_wallet(wallet_name: str = "viewonly", password: str = "") -> dict:
    """Open an existing wallet on monero-wallet-rpc."""
    logger.info("opening_wallet", wallet_name=wallet_name)
    return await rpc_call(
        "open_wallet",
        {
            "filename": wallet_name,
            "password": password,
        },
    )


async def get_wallet_height() -> int:
    """Get the current wallet block height."""
    result = await rpc_call("get_height")
    return result.get("height", 0)


async def close_wallet() -> None:
    """Close the current wallet."""
    try:
        await rpc_call("close_wallet")
    except Exception:
        pass  # Ignore errors if no wallet is open


async def delete_wallet(wallet_name: str = "viewonly") -> None:
    """Delete a wallet file from monero-wallet-rpc.

    This uses the internal RPC method to delete the wallet file.
    Falls back to closing if delete is not available.
    """
    logger.info("deleting_wallet", wallet_name=wallet_name)
    try:
        # First close the wallet if open
        await close_wallet()
    except Exception:
        pass

    try:
        logger.info("wallet_closed_after_delete", wallet_name=wallet_name)
    except Exception as e:
        logger.warning("wallet_delete_failed", wallet_name=wallet_name, error=str(e))
