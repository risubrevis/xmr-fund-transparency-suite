"""Seed test giveaways (raffles) with realistic lifecycle states.

Creates several giveaways on an existing wallet (or creates one if none
exist), spread across the four lifecycle states relative to "now":

  * ended   — start/end both in the past, filled with eligible transactions
              (awaiting "Pick Winner").
  * closed  — ended, plus a fabricated winner record so the winner-announcement
              UI state is testable. The seed block hash/height are fake.
  * active  — start in the past, end in the future, filled with transactions
              dated within [start, now].
  * future  — start/end both in the future, NO transactions (a scheduled
              giveaway has no entries yet).

Every seeded transaction is >= the giveaway's min_amount_xmr and falls within
[start_date, end_date], so all of them count as eligible entries.

Idempotent: existing giveaways (matched by wallet_id + title) are skipped, so
the script is safe to run repeatedly.

Usage:
    python -m tests.seed_giveaways

Run inside the backend container where DATABASE_URL is auto-configured.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.crypto import ViewKeyEncryption
from app.database import async_session_factory
from app.models import Giveaway, Transaction, Wallet

PICONERO = Decimal("1e12")
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# Deterministic RNG so repeated runs produce identical addresses/configs
# (but new txids, since those must be unique).
RNG = random.Random(20260721)


def hex_id() -> str:
    """64-char hex string (used for txids and fake block hashes)."""
    return uuid.uuid4().hex + uuid.uuid4().hex


def generate_deposit_address(seed: str) -> str:
    """Deterministic valid-format Monero subaddress (prefix '8', 95 chars)."""
    rng = random.Random(seed)
    addr = "8"
    for _ in range(94):
        addr += rng.choice(B58_ALPHABET)
    return addr


def varied_amount(min_amount: Decimal) -> tuple[int, Decimal]:
    """Return (atomic, xmr) >= min_amount with a realistic spread."""
    r = RNG.random()
    if r < 0.6:
        # just above the threshold up to 3x
        factor = Decimal(str(1 + RNG.random() * 2))
    elif r < 0.9:
        # 3x .. 10x
        factor = Decimal(str(3 + RNG.random() * 7))
    else:
        # whale: 10x .. 40x
        factor = Decimal(str(10 + RNG.random() * 30))
    amount_xmr = (min_amount * factor).quantize(Decimal("0.000000000001"))
    amount_atomic = int(amount_xmr * PICONERO)
    return amount_atomic, amount_xmr


# Each config is relative to "now" via timedelta offsets (days/hours).
# tx_count=0 means "future" (no transactions).
GIVEAWAY_CONFIGS: list[dict] = [
    # ── Ended (awaiting Pick Winner) ──────────────────────────────────────
    {
        "title": "Expired Tech Bundle Giveaway",
        "description": "A tech gadget bundle — ended, awaiting winner selection.",
        "min_amount_xmr": Decimal("0.1"),
        "start": timedelta(days=-10),
        "end": timedelta(days=-2),
        "tx_count": 9,
        "closed": False,
    },
    {
        "title": "Expired Art Commission Raffle",
        "description": "Custom art commission prize. Ended recently.",
        "min_amount_xmr": Decimal("0.5"),
        "start": timedelta(days=-30),
        "end": timedelta(days=-1),
        "tx_count": 6,
        "closed": False,
    },
    # ── Closed (fabricated winner, for UI winner-view testing) ─────────────
    {
        "title": "Closed Beta Key Giveaway",
        "description": "Closed beta keys — winner already selected (seed data).",
        "min_amount_xmr": Decimal("0.05"),
        "start": timedelta(days=-20),
        "end": timedelta(days=-5),
        "tx_count": 11,
        "closed": True,
    },
    # ── Active (running) ──────────────────────────────────────────────────
    {
        "title": "Active Streamer Support Giveaway",
        "description": "Live now — donate to enter, winner picked at close.",
        "min_amount_xmr": Decimal("0.1"),
        "start": timedelta(days=-3),
        "end": timedelta(days=4),
        "tx_count": 12,
        "closed": False,
    },
    {
        "title": "Active NFT Raffle",
        "description": "Active NFT raffle — entries open.",
        "min_amount_xmr": Decimal("0.25"),
        "start": timedelta(days=-1),
        "end": timedelta(days=2),
        "tx_count": 7,
        "closed": False,
    },
    # ── Future (scheduled, no entries yet) ────────────────────────────────
    {
        "title": "Future Conference Pass Giveaway",
        "description": "Conference pass raffle — starts soon.",
        "min_amount_xmr": Decimal("0.1"),
        "start": timedelta(days=3),
        "end": timedelta(days=10),
        "tx_count": 0,
        "closed": False,
    },
    {
        "title": "Future Merch Bundle Giveaway",
        "description": "Merch bundle — scheduled for next week.",
        "min_amount_xmr": Decimal("0.05"),
        "start": timedelta(days=1),
        "end": timedelta(days=5),
        "tx_count": 0,
        "closed": False,
    },
]


async def _ensure_wallet(session) -> Wallet:
    """Reuse the first existing wallet, or create a dedicated one."""
    result = await session.execute(select(Wallet).limit(1))
    wallet = result.scalar_one_or_none()
    if wallet is not None:
        return wallet

    cipher = ViewKeyEncryption("changeme")
    wallet = Wallet(
        name="Giveaway Test Wallet",
        primary_address="4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ",
        view_key=cipher.encrypt("a" * 64),
        start_height=3_280_000,
        is_active=True,
    )
    session.add(wallet)
    await session.flush()
    print(f"  Created wallet: {wallet.name} ({wallet.id})")
    return wallet


async def seed() -> None:
    async with async_session_factory() as session:
        wallet = await _ensure_wallet(session)
        now = datetime.now(timezone.utc)

        # Skip giveaways already seeded (idempotency).
        result = await session.execute(
            select(Giveaway).where(Giveaway.wallet_id == wallet.id)
        )
        existing = {g.title for g in result.scalars().all()}

        total_txs = 0
        created = 0
        skipped = 0

        for cfg in GIVEAWAY_CONFIGS:
            if cfg["title"] in existing:
                print(f"  Skip existing giveaway: {cfg['title']}")
                skipped += 1
                continue

            start_dt = now + cfg["start"]
            end_dt = now + cfg["end"]
            deposit_addr = generate_deposit_address(f"giveaway-{cfg['title']}")

            giveaway = Giveaway(
                wallet_id=wallet.id,
                title=cfg["title"],
                description=cfg["description"],
                deposit_address=deposit_addr,
                min_amount_xmr=cfg["min_amount_xmr"],
                start_date=start_dt,
                end_date=end_dt,
                instructions_after_end=(
                    "Email the organizer with your winning txid to claim your prize."
                ),
                is_active=True,
            )
            session.add(giveaway)
            await session.flush()
            created += 1

            # Determine the status for logging.
            if cfg["closed"]:
                state = "closed"
            elif now < start_dt:
                state = "scheduled"
            elif now < end_dt:
                state = "active"
            else:
                state = "ended"
            print(
                f"  Created giveaway [{state}] '{cfg['title']}' "
                f"min={cfg['min_amount_xmr']} XMR "
                f"{start_dt:%Y-%m-%d}→{end_dt:%Y-%m-%d}"
            )

            if cfg["tx_count"] == 0:
                continue

            # Transactions must be within [start, end] and (for active ones)
            # cannot be in the future, so cap the window at now.
            window_end = min(end_dt, now)
            span_seconds = max(1, int((window_end - start_dt).total_seconds()))
            txs: list[Transaction] = []
            for _ in range(cfg["tx_count"]):
                amount_atomic, amount_xmr = varied_amount(cfg["min_amount_xmr"])
                offset = RNG.uniform(0, span_seconds)
                ts = start_dt + timedelta(seconds=offset)
                txs.append(
                    Transaction(
                        fund_id=None,
                        giveaway_id=giveaway.id,
                        wallet_id=wallet.id,
                        txid=hex_id(),
                        amount_atomic=amount_atomic,
                        amount_xmr=amount_xmr,
                        confirmations=RNG.randint(1, 1000),
                        timestamp=ts,
                        unlock_time=0,
                        height=RNG.randint(3_700_000, 3_720_000),
                    )
                )
            session.add_all(txs)
            total_txs += len(txs)

            # For the closed config: fabricate a winner so the winner-announcement
            # UI is testable. The seed block hash/height are synthetic (not a real
            # Monero block) — this is test data only.
            if cfg["closed"]:
                await session.flush()  # ensure txs have ids
                winner = txs[len(txs) // 2]  # deterministic middle entry
                giveaway.winning_transaction_id = winner.id
                giveaway.winning_block_hash = hex_id()
                giveaway.winning_block_height = RNG.randint(3_700_000, 3_720_000)
                giveaway.is_closed = True

        await session.commit()

        print(
            f"\nDone! Giveaways created: {created}, skipped: {skipped}, "
            f"transactions inserted: {total_txs}"
        )

        # Summary
        result = await session.execute(
            select(Giveaway).where(Giveaway.wallet_id == wallet.id)
        )
        all_giveaways = result.scalars().all()
        print("\n--- Giveaways summary ---")
        for g in all_giveaways:
            tag = (
                "CLOSED"
                if g.is_closed
                else (
                    "scheduled"
                    if now < g.start_date
                    else "active" if now < g.end_date else "ended"
                )
            )
            print(
                f"  • [{tag:9}] {g.title}  min={g.min_amount_xmr} XMR  "
                f"{g.start_date:%Y-%m-%d}→{g.end_date:%Y-%m-%d}"
            )


if __name__ == "__main__":
    asyncio.run(seed())
