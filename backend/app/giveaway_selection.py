"""Provably-fair giveaway winner selection.

The winner is chosen deterministically from the pool of eligible
transactions using the hash of the first Monero block mined strictly
after the giveaway's end_date as an unpredictable seed. Because no
party could know that block's hash before end_date, the result is
unbiased and publicly verifiable.

Algorithm:
  1. Eligible pool = transactions to the giveaway's deposit_address
     with start_date <= timestamp <= end_date and amount >= min_amount.
  2. Seed = first block after end_date (hash + height) from the daemon.
  3. score(tx) = sha256(block_hash || txid).hexdigest(); lowest score wins.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.daemon_rpc import BlockHeader, DaemonRPCClient
from app.logging import get_logger
from app.models import Giveaway, Transaction

logger = get_logger("app.giveaway_selection")


class WinnerSelectionError(Exception):
    """Raised when winner selection cannot be completed."""


@dataclass
class WinnerResult:
    winning_transaction: Transaction | None
    block_header: BlockHeader
    eligible_count: int


def _score(block_hash: str, txid: str) -> bytes:
    """Deterministic 32-byte score for a transaction under a seed block."""
    return hashlib.sha256(f"{block_hash}{txid}".encode()).digest()


async def select_winner(
    giveaway: Giveaway,
    db: AsyncSession,
    daemon: DaemonRPCClient | None = None,
) -> WinnerResult:
    """Compute the provably-fair winner for a closed giveaway.

    Does NOT persist the result; the caller is responsible for storing
    winning_transaction_id / winning_block_hash / winning_block_height
    and setting is_closed=True.
    """
    end_ts = int(giveaway.end_date.astimezone(timezone.utc).timestamp())

    if daemon is None:
        daemon = DaemonRPCClient()

    block = await daemon.find_first_block_after(end_ts)
    if block is None:
        raise WinnerSelectionError(
            "No block has been mined after the giveaway end date yet. "
            "Wait for the next Monero block to be mined and try again."
        )

    # Eligible pool: within [start_date, end_date] and amount >= min_amount.
    rows = await db.execute(
        select(Transaction).where(
            Transaction.giveaway_id == giveaway.id,
            Transaction.timestamp >= giveaway.start_date,
            Transaction.timestamp <= giveaway.end_date,
            Transaction.amount_xmr >= Decimal(giveaway.min_amount_xmr),
        )
    )
    eligible = list(rows.scalars().all())

    if not eligible:
        # No valid entries — close with no winner.
        return WinnerResult(
            winning_transaction=None,
            block_header=block,
            eligible_count=0,
        )

    # Deterministic ranking by score; lowest digest wins. Ties broken by
    # txid (lexicographic) for a fully deterministic ordering.
    ranked = sorted(
        eligible,
        key=lambda tx: (_score(block.hash, tx.txid), tx.txid),
    )
    winner = ranked[0]

    logger.info(
        "giveaway_winner_selected",
        giveaway_id=str(giveaway.id),
        winner_txid=winner.txid,
        seed_height=block.height,
        seed_hash=block.hash,
        eligible_count=len(eligible),
    )

    return WinnerResult(
        winning_transaction=winner,
        block_header=block,
        eligible_count=len(eligible),
    )


def verify_score(block_hash: str, txid: str) -> str:
    """Public helper exposing the scoring function for verification UI."""
    return _score(block_hash, txid).hex()
