"""Tests for the provably-fair giveaway winner selection."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.daemon_rpc import BlockHeader, DaemonRPCClient
from app.giveaway_selection import select_winner
from app.models import Giveaway, Transaction


def _make_giveaway(min_amount="0.05", end_offset_minutes=0) -> Giveaway:
    now = datetime.now(timezone.utc)
    return Giveaway(
        id=uuid.uuid4(),
        public_uuid=str(uuid.uuid4()),
        wallet_id=uuid.uuid4(),
        title="T",
        description=None,
        deposit_address="8" + "A" * 94,
        min_amount_xmr=Decimal(min_amount),
        start_date=now - timedelta(hours=2),
        end_date=now - timedelta(minutes=end_offset_minutes),
        instructions_after_end=None,
        widget_background_color=None,
        widget_text_color=None,
        public_website=None,
        winning_transaction_id=None,
        winning_block_hash=None,
        winning_block_height=None,
        is_closed=False,
        created_at=now,
    )


def _make_tx(
    giveaway: Giveaway, txid: str, amount: str, minutes_ago: int
) -> Transaction:
    return Transaction(
        id=uuid.uuid4(),
        fund_id=None,
        giveaway_id=giveaway.id,
        wallet_id=giveaway.wallet_id,
        txid=txid,
        amount_atomic=int(Decimal(amount) * 10**12),
        amount_xmr=Decimal(amount),
        confirmations=10,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
        unlock_time=0,
        height=1000,
    )


class FakeDaemon(DaemonRPCClient):
    def __init__(self, seed_hash: str, seed_height: int, seed_ts: int):
        self._seed = BlockHeader(seed_height, seed_hash, seed_ts)
        self._chain = seed_height + 1

    async def get_chain_height(self) -> int:
        return self._chain

    async def get_block_header_by_height(self, height: int) -> BlockHeader:
        return self._seed

    async def find_first_block_after(self, target_ts: int) -> BlockHeader | None:
        return self._seed

    async def close(self) -> None:
        pass


def _build_db_with_txs(txs: list[Transaction]) -> MagicMock:
    db = MagicMock()
    # select_winner runs: select(Transaction).where(...)
    result = MagicMock()
    result.scalars.return_value.all.return_value = txs
    db.execute = AsyncMock(return_value=result)
    return db


@pytest.mark.asyncio
async def test_select_winner_picks_lowest_score():
    giveaway = _make_giveaway()
    a = _make_tx(giveaway, "a" * 64, "0.06", 90)
    b = _make_tx(giveaway, "b" * 64, "0.10", 60)
    # Below min amount -> ineligible
    c = _make_tx(giveaway, "c" * 64, "0.02", 30)
    db = _build_db_with_txs([a, b, c])

    seed_hash = "deadbeef" * 8
    seed_height = 3722370
    daemon = FakeDaemon(
        seed_hash, seed_height, int(datetime.now(timezone.utc).timestamp())
    )

    result = await select_winner(giveaway, db, daemon=daemon)

    expected_scores = {
        a.txid: hashlib.sha256(f"{seed_hash}{a.txid}".encode()).digest(),
        b.txid: hashlib.sha256(f"{seed_hash}{b.txid}".encode()).digest(),
        c.txid: hashlib.sha256(f"{seed_hash}{c.txid}".encode()).digest(),
    }
    lowest = sorted(expected_scores.items(), key=lambda kv: (kv[1], kv[0]))[0][0]
    assert result.winning_transaction.txid == lowest
    assert result.block_header.hash == seed_hash
    assert result.block_header.height == seed_height


@pytest.mark.asyncio
async def test_select_winner_no_eligible_entries():
    giveaway = _make_giveaway()
    db = _build_db_with_txs([])  # no transactions
    daemon = FakeDaemon("ab" * 32, 100, int(datetime.now(timezone.utc).timestamp()))
    result = await select_winner(giveaway, db, daemon=daemon)
    assert result.winning_transaction is None
    assert result.eligible_count == 0
    assert result.block_header.hash == "ab" * 32
