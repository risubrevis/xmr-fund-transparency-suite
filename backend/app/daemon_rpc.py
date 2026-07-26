"""Client for Monero daemon JSON-RPC.

Used by the giveaway winner-selection logic to read block headers
(block hash + timestamp) from the chain, which act as an unpredictable,
publicly-verifiable random seed.

The monero-wallet-rpc does NOT expose block-header lookups, so this
talks to the daemon directly. The daemon URL is derived from settings
(see ``app.config.Settings.daemon_rpc_url``).
"""

from __future__ import annotations

import httpx

from app.config import settings
from app.logging import get_logger

logger = get_logger("app.daemon_rpc")


class BlockHeader:
    __slots__ = ("height", "hash", "timestamp")

    def __init__(self, height: int, hash: str, timestamp: int) -> None:
        self.height = height
        self.hash = hash
        self.timestamp = timestamp


class DaemonRPCError(RuntimeError):
    pass


class DaemonRPCClient:
    """Thin async JSON-RPC client for the Monero daemon."""

    def __init__(self, rpc_url: str | None = None, timeout: float = 30.0) -> None:
        self.rpc_url = (rpc_url or settings.daemon_rpc_url).rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def _call(self, method: str, params: dict | None = None) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": method,
            "params": params or {},
        }
        client = await self._get_client()
        r = await client.post(self.rpc_url, json=payload)
        r.raise_for_status()
        data = r.json()
        if "error" in data and data["error"]:
            raise DaemonRPCError(str(data["error"].get("message", data["error"])))
        return data.get("result", {})

    async def get_chain_height(self) -> int:
        """Return the current chain tip height (last mined block height + 1).

        Uses get_info.height (top block height + 1 == current chain height).
        """
        result = await self._call("get_info")
        return int(result["height"])

    async def get_block_header_by_height(self, height: int) -> BlockHeader:
        result = await self._call("get_block_header_by_height", {"height": height})
        header = result["block_header"]
        return BlockHeader(
            height=int(header["height"]),
            hash=str(header["hash"]),
            timestamp=int(header["timestamp"]),
        )

    async def find_first_block_after(self, target_ts: int) -> BlockHeader | None:
        """Return the first block mined strictly after ``target_ts`` (unix).

        Block timestamps are monotonic non-decreasing, so we binary search.
        Returns None if the chain tip's timestamp is still <= target_ts
        (i.e. no block past that time has been mined yet).
        """
        chain_height = await self.get_chain_height()
        # chain_height is the count of blocks (top block index = height - 1).
        if chain_height <= 0:
            return None
        top = await self.get_block_header_by_height(chain_height - 1)
        if top.timestamp <= target_ts:
            return None

        # Standard binary search for the leftmost block with timestamp > target_ts.
        lo = 0
        hi = chain_height - 1
        first_after = top
        while lo <= hi:
            mid = (lo + hi) // 2
            mid_header = await self.get_block_header_by_height(mid)
            if mid_header.timestamp > target_ts:
                first_after = mid_header
                hi = mid - 1
            else:
                lo = mid + 1
        return first_after

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
