"""Comprehensive test-data seeder for the XMR Fund Transparency Suite.

Wipes all application tables, then creates a realistic dataset:

  * 3 wallets
  * per wallet: 2 funds (with targets) + 4 giveaways spanning all lifecycle
    states (ended / closed / active / future)
  * per fund AND per giveaway: several news posts
  * per fund: transactions whose total stays below the fund's target amount
  * per non-future giveaway: eligible transactions (>= min_amount, within the
    [start, end] window); the closed giveaway also gets a fabricated winner so
    the winner-announcement UI is testable

Idempotent in the sense that every run starts from a clean slate (TRUNCATE),
so it is safe to run repeatedly via `./scripts/test-data.sh`.

Run inside the backend container where DATABASE_URL is auto-configured.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, text

from app.crypto import ViewKeyEncryption
from app.database import async_session_factory
from app.models import Fund, Giveaway, Post, Transaction, Wallet

PICONERO = Decimal("1e12")
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def info(msg: str) -> None:
    print(f"→ {msg}")


def ok(msg: str) -> None:
    print(f"✓ {msg}")


# Deterministic RNG → identical dataset on every run (txids are still unique).
RNG = random.Random(20260722)


def hex_id() -> str:
    """64-char hex string for txids and fabricated block hashes."""
    return uuid.uuid4().hex + uuid.uuid4().hex


def gen_address(seed: str, prefix: str = "4") -> str:
    """Deterministic valid-format Monero address (95 chars, base58)."""
    rng = random.Random(seed)
    addr = prefix
    for _ in range(94):
        addr += rng.choice(B58_ALPHABET)
    return addr


def varied_amount(min_amount: Decimal) -> tuple[int, Decimal]:
    """Return (atomic, xmr) >= min_amount with a realistic spread."""
    r = RNG.random()
    if r < 0.6:
        factor = Decimal(str(1 + RNG.random() * 2))  # 1x..3x
    elif r < 0.9:
        factor = Decimal(str(3 + RNG.random() * 7))  # 3x..10x
    else:
        factor = Decimal(str(10 + RNG.random() * 30))  # 10x..40x
    amount_xmr = (min_amount * factor).quantize(Decimal("0.000000000001"))
    return int(amount_xmr * PICONERO), amount_xmr


def random_txs_within_budget(
    wallet_id: uuid.UUID,
    fund_id: uuid.UUID,
    target_xmr: Decimal,
    count: int,
) -> list[Transaction]:
    """Generate `count` fund transactions whose total is 50–95% of the target.

    The fund's recorded received XMR therefore never exceeds its goal.
    """
    desired_total = target_xmr * Decimal(str(RNG.uniform(0.5, 0.95)))
    # Random weights, scaled to the desired total.
    weights = [Decimal(str(RNG.random())) + Decimal("0.01") for _ in range(count)]
    weight_sum = sum(weights)
    now = datetime.now(timezone.utc)
    txs: list[Transaction] = []
    for i, w in enumerate(weights):
        amount_xmr = (desired_total * w / weight_sum).quantize(
            Decimal("0.000000000001")
        )
        amount_atomic = int(amount_xmr * PICONERO)
        txs.append(
            Transaction(
                fund_id=fund_id,
                wallet_id=wallet_id,
                txid=hex_id(),
                amount_atomic=amount_atomic,
                amount_xmr=amount_xmr,
                confirmations=RNG.randint(1, 1000),
                timestamp=now
                - timedelta(
                    days=RNG.randint(0, 365),
                    hours=RNG.randint(0, 23),
                    minutes=RNG.randint(0, 59),
                ),
                unlock_time=0,
                height=RNG.randint(3_700_000, 3_720_000),
            )
        )
    return txs


# Per-wallet config: name, primary address, funds (label, description, target),
# and giveaway templates. Giveaway dates are relative to "now" (timedelta).
WALLET_CONFIGS: list[dict] = [
    {
        "name": "Community Donations",
        "primary_address": "4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ",
        "funds": [
            (
                "General Fund",
                "Community donations for ongoing development",
                Decimal("500"),
            ),
            ("Infrastructure Fund", "Hosting, domains, infrastructure", Decimal("200")),
        ],
        "giveaways": [
            (
                "Expired Tech Bundle",
                "Tech gadget bundle — ended.",
                Decimal("0.1"),
                -10,
                -2,
                9,
                "ended",
            ),
            (
                "Closed Beta Keys",
                "Beta keys — winner selected (seed data).",
                Decimal("0.05"),
                -20,
                -5,
                11,
                "closed",
            ),
            (
                "Active Streamer Support",
                "Live now — donate to enter.",
                Decimal("0.1"),
                -3,
                4,
                12,
                "active",
            ),
            (
                "Future Conference Pass",
                "Conference pass — starts soon.",
                Decimal("0.1"),
                3,
                10,
                0,
                "future",
            ),
        ],
    },
    {
        "name": "CCS Proposals",
        "primary_address": "44AFFq5kSiGBoF4shVDBqAXT8v2KtfY5fJzM3X6XLxWjUYQxFxJMY5RF1R6ZRZ2VaqMTQz2k2V7HvqmdFVM5Y4L1aSgJMM",
        "funds": [
            ("GUI Development", "Monero GUI wallet improvements", Decimal("750")),
            ("Research Fund", "Privacy research support", Decimal("1000")),
        ],
        "giveaways": [
            (
                "Expired Art Commission",
                "Custom art commission — ended.",
                Decimal("0.5"),
                -30,
                -1,
                6,
                "ended",
            ),
            (
                "Closed NFT Drop",
                "NFT drop — winner selected (seed data).",
                Decimal("0.25"),
                -15,
                -3,
                8,
                "closed",
            ),
            (
                "Active Hackathon Bounties",
                "Active raffle for bounty winners.",
                Decimal("0.2"),
                -2,
                5,
                10,
                "active",
            ),
            (
                "Future Workshop Seat",
                "Workshop seat — scheduled.",
                Decimal("0.1"),
                5,
                14,
                0,
                "future",
            ),
        ],
    },
    {
        "name": "Streamer Donations",
        "primary_address": "47sw7ZZa3DnV2S2sYbyVuaNC7ahM7VdBxQdKkQ5RDx8U4VJFY5wGQ6YQgM5PjRvC1F6Zz4V4FfGz3fYh8qM5b3hK9Vd7W",
        "funds": [
            ("Stream Support", "Direct stream support", Decimal("50")),
            ("Charity Streams", "100% to the selected charity", Decimal("300")),
        ],
        "giveaways": [
            (
                "Expired Merch Drop",
                "Merch drop — ended.",
                Decimal("0.05"),
                -8,
                -1,
                7,
                "ended",
            ),
            (
                "Closed VIP Meetup",
                "VIP meetup — winner selected (seed data).",
                Decimal("0.5"),
                -12,
                -2,
                9,
                "closed",
            ),
            (
                "Active Subathon Goal",
                "Active subathon raffle.",
                Decimal("0.1"),
                -1,
                3,
                11,
                "active",
            ),
            (
                "Future Anniversary Giveaway",
                "Anniversary giveaway — scheduled.",
                Decimal("0.05"),
                2,
                8,
                0,
                "future",
            ),
        ],
    },
]


# Realistic post body templates. `{target}` is replaced with the fund/giveaway
# name; dates are interpolated too.
POST_TEMPLATES = [
    "Thanks to everyone supporting {target} — we just hit a new milestone!",
    "Quick update on {target}: we've added new reward tiers. Check the widget.",
    "Reminder: {target} entries close soon. Don't miss out!",
    "Q&A thread for {target} — ask anything in the comments.",
    "Behind the scenes of {target}: a look at where your donations go.",
    "Milestone reached for {target}! Thank you, community.",
    "New stretch goal announced for {target}.",
]


def make_post_body(target_name: str) -> str:
    return RNG.choice(POST_TEMPLATES).replace("{target}", target_name)


def giveaway_txs(
    wallet_id: uuid.UUID,
    giveaway_id: uuid.UUID,
    min_amount: Decimal,
    start_dt: datetime,
    end_dt: datetime,
    tx_count: int,
    state: str,
) -> list[Transaction]:
    if tx_count == 0:
        return []
    now = datetime.now(timezone.utc)
    window_end = min(end_dt, now)
    span_seconds = max(1, int((window_end - start_dt).total_seconds()))
    txs: list[Transaction] = []
    for _ in range(tx_count):
        amount_atomic, amount_xmr = varied_amount(min_amount)
        offset = RNG.uniform(0, span_seconds)
        ts = start_dt + timedelta(seconds=offset)
        txs.append(
            Transaction(
                fund_id=None,
                giveaway_id=giveaway_id,
                wallet_id=wallet_id,
                txid=hex_id(),
                amount_atomic=amount_atomic,
                amount_xmr=amount_xmr,
                confirmations=RNG.randint(1, 1000),
                timestamp=ts,
                unlock_time=0,
                height=RNG.randint(3_700_000, 3_720_000),
            )
        )
    return txs


def make_posts(
    wallet_id: uuid.UUID,
    fund_id: uuid.UUID | None,
    giveaway_id: uuid.UUID | None,
    target_name: str,
    count: int,
) -> list[Post]:
    now = datetime.now(timezone.utc)
    posts: list[Post] = []
    for i in range(count):
        # Make the most recent post fresh (within 24h) so the widget's
        # "fresh news" badge is visible in the demo; the rest span a month.
        if i == 0:
            created = now - timedelta(
                hours=RNG.randint(0, 23), minutes=RNG.randint(0, 59)
            )
        else:
            created = now - timedelta(days=RNG.randint(1, 30), hours=RNG.randint(0, 23))
        posts.append(
            Post(
                fund_id=fund_id,
                giveaway_id=giveaway_id,
                wallet_id=wallet_id,
                body=make_post_body(target_name),
                created_at=created,
            )
        )
    return posts


async def seed() -> None:
    async with async_session_factory() as session:
        # ── Wipe all application data ──────────────────────────────────────
        info("Wiping database (wallets, funds, giveaways, transactions, posts)...")
        await session.execute(
            text(
                "TRUNCATE wallets, funds, giveaways, transactions, posts "
                "RESTART IDENTITY CASCADE"
            )
        )
        await session.commit()

        cipher = ViewKeyEncryption("changeme")
        now = datetime.now(timezone.utc)

        total_wallets = 0
        total_funds = 0
        total_giveaways = 0
        total_posts = 0
        total_txs = 0

        for wi, cfg in enumerate(WALLET_CONFIGS):
            fake_vk = "".join(chr(ord("a") + (wi + j) % 26) for j in range(64))
            wallet = Wallet(
                name=cfg["name"],
                primary_address=cfg["primary_address"],
                view_key=cipher.encrypt(fake_vk),
                start_height=3_280_000,
                is_active=True,
            )
            session.add(wallet)
            await session.flush()
            total_wallets += 1
            info(f"Wallet: {wallet.name}")

            # ── Funds ──────────────────────────────────────────────────────
            for label, desc, target in cfg["funds"]:
                fund = Fund(
                    wallet_id=wallet.id,
                    label=label,
                    description=desc,
                    deposit_address=gen_address(f"fund-{cfg['name']}-{label}"),
                    is_active=True,
                    target_amount_xmr=target,
                )
                session.add(fund)
                await session.flush()
                total_funds += 1

                txs = random_txs_within_budget(wallet.id, fund.id, target, count=20)
                session.add_all(txs)
                total_txs += len(txs)

                posts = make_posts(
                    wallet.id, fund.id, None, label, count=RNG.randint(3, 5)
                )
                session.add_all(posts)
                total_posts += len(posts)

                received = sum(t.amount_xmr for t in txs)
                info(
                    f"  Fund: {label} (target {target} XMR, received "
                    f"{received:.4f} XMR, {len(txs)} txs, {len(posts)} posts)"
                )

            # ── Giveaways ─────────────────────────────────────────────────
            for (
                gtitle,
                gdesc,
                gmin,
                gstart_days,
                gend_days,
                gtx_count,
                gstate,
            ) in cfg["giveaways"]:
                start_dt = now + timedelta(days=gstart_days)
                end_dt = now + timedelta(days=gend_days)
                giveaway = Giveaway(
                    wallet_id=wallet.id,
                    title=gtitle,
                    description=gdesc,
                    deposit_address=gen_address(
                        f"giveaway-{cfg['name']}-{gtitle}", prefix="8"
                    ),
                    min_amount_xmr=gmin,
                    start_date=start_dt,
                    end_date=end_dt,
                    instructions_after_end=(
                        "Email the organizer with your winning txid to claim "
                        "your prize."
                    ),
                    is_active=True,
                )
                session.add(giveaway)
                await session.flush()
                total_giveaways += 1

                gtxs = giveaway_txs(
                    wallet.id, giveaway.id, gmin, start_dt, end_dt, gtx_count, gstate
                )
                session.add_all(gtxs)
                total_txs += len(gtxs)

                # Posts for every giveaway (including future ones — news can
                # predate the start date).
                gposts = make_posts(
                    wallet.id, None, giveaway.id, gtitle, count=RNG.randint(3, 5)
                )
                session.add_all(gposts)
                total_posts += len(gposts)

                # Fabricate a winner for closed giveaways (test data only —
                # the seed block hash/height are synthetic, not a real block).
                if gstate == "closed" and gtxs:
                    await session.flush()
                    winner = gtxs[len(gtxs) // 2]
                    giveaway.winning_transaction_id = winner.id
                    giveaway.winning_block_hash = hex_id()
                    giveaway.winning_block_height = RNG.randint(3_700_000, 3_720_000)
                    giveaway.is_closed = True

                info(
                    f"  Giveaway [{gstate:9}] {gtitle} (min {gmin} XMR, "
                    f"{len(gtxs)} txs, {len(gposts)} posts)"
                )

        await session.commit()

        print()
        ok(
            f"Done! wallets={total_wallets} funds={total_funds} "
            f"giveaways={total_giveaways} posts={total_posts} "
            f"transactions={total_txs}"
        )

        # ── Summary with invariant checks ─────────────────────────────────
        result = await session.execute(select(Fund))
        funds = result.scalars().all()
        result = await session.execute(select(Giveaway))
        giveaways = result.scalars().all()
        result = await session.execute(select(Transaction))
        txs = result.scalars().all()

        print("\n--- Invariant checks ---")
        ok_count = 0
        for f in funds:
            received = sum(t.amount_xmr for t in txs if t.fund_id == f.id)
            ok_flag = received <= (f.target_amount_xmr or Decimal("0"))
            ok_count += ok_flag
            print(
                f"  fund '{f.label}': received {received:.4f} <= "
                f"target {f.target_amount_xmr} → {'OK' if ok_flag else 'FAIL'}"
            )
        for g in giveaways:
            state = (
                "closed"
                if g.is_closed
                else (
                    "scheduled"
                    if now < g.start_date
                    else "active" if now < g.end_date else "ended"
                )
            )
            gtxs = [t for t in txs if t.giveaway_id == g.id]
            below = sum(1 for t in gtxs if t.amount_xmr < g.min_amount_xmr)
            outside = sum(
                1
                for t in gtxs
                if t.timestamp < g.start_date or t.timestamp > g.end_date
            )
            ok_flag = below == 0 and outside == 0
            ok_count += ok_flag
            print(
                f"  giveaway [{state:9}] '{g.title}': {len(gtxs)} txs, "
                f"below_min={below}, outside_dates={outside} → "
                f"{'OK' if ok_flag else 'FAIL'}"
            )
        print(f"\n{ok_count}/{len(funds) + len(giveaways)} invariants OK")


if __name__ == "__main__":
    asyncio.run(seed())
