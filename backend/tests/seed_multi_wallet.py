"""Seed multiple wallets, funds, and transactions for multi-wallet testing.

Creates 3 wallets, each with 2 funds, and populates each fund with random
transactions spanning the last year. Safe to run multiple times — checks
for existing data and only creates what's missing.

Usage:
    python -m tests.seed_multi_wallet [--count=N]

Environment variables (DATABASE_URL) must be set or this runs inside
the backend Docker container where they are auto-configured.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.crypto import ViewKeyEncryption
from app.database import async_session_factory
from app.models import Fund, Transaction, Wallet
from sqlalchemy import select

PICONERO = Decimal("1e12")

# Each wallet gets a name, primary address, and list of funds.
# Deposit addresses are auto-generated to be unique.
WALLET_CONFIGS = [
    {
        "name": "Community Donations",
        "primary_address": "4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ",
        "funds": [
            {
                "label": "General Fund",
                "description": "Community donations for ongoing development and maintenance",
                "target_amount_xmr": Decimal("500"),
            },
            {
                "label": "Infrastructure Fund",
                "description": "Server hosting, domain names, and infrastructure costs",
                "target_amount_xmr": Decimal("200"),
            },
        ],
    },
    {
        "name": "CCS Proposals",
        "primary_address": "44AFFq5kSiGBoF4shVDBqAXT8v2KtfY5fJzM3X6XLxWjUYQxFxJMY5RF1R6ZRZ2VaqMTQz2k2V7HvqmdFVM5Y4L1aSgJMM",
        "funds": [
            {
                "label": "GUI Development",
                "description": "Funding for Monero GUI wallet improvements and new features",
                "target_amount_xmr": Decimal("750"),
            },
            {
                "label": "Research Fund",
                "description": "Privacy research and academic collaboration support",
                "target_amount_xmr": Decimal("1000"),
            },
        ],
    },
    {
        "name": "Streamer Donations",
        "primary_address": "47sw7ZZa3DnV2S2sYbyVuaNC7ahM7VdBxQdKkQ5RDx8U4VJFY5wGQ6YQgM5PjRvC1F6Zz4V4FfGz3fYh8qM5b3hK9Vd7W",
        "funds": [
            {
                "label": "Stream Support",
                "description": "Direct support for streaming activities and content creation",
                "target_amount_xmr": Decimal("50"),
            },
            {
                "label": "Charity Streams",
                "description": "Charity stream donations — 100% goes to the selected charity",
                "target_amount_xmr": Decimal("300"),
            },
        ],
    },
]

# Base58 alphabet used by Monero addresses
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def generate_deposit_address(seed: str) -> str:
    """Generate a deterministic unique Monero-format address from a seed.

    Not a real address — just valid format (starts with '4', 95 chars, base58).
    """
    rng = random.Random(seed)
    # Start with '4' (standard mainnet address prefix)
    addr = "4"
    for _ in range(94):
        addr += rng.choice(B58_ALPHABET)
    return addr


def random_txid() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex


def random_amount() -> tuple[int, Decimal]:
    """Return (atomic, xmr) pair with varied distribution across tiers."""
    tier = random.random()
    if tier < 0.45:
        # micro: 0.001–0.1 XMR
        amount_atomic = random.randint(1_000_000_000, 100_000_000_000)
    elif tier < 0.75:
        # medium: 0.1–1.0 XMR
        amount_atomic = random.randint(100_000_000_000, 1_000_000_000_000)
    elif tier < 0.92:
        # large: 1.0–5.0 XMR
        amount_atomic = random.randint(1_000_000_000_000, 5_000_000_000_000)
    else:
        # whale: 5.0–50.0 XMR
        amount_atomic = random.randint(5_000_000_000_000, 50_000_000_000_000)
    amount_xmr = Decimal(amount_atomic) / PICONERO
    return amount_atomic, amount_xmr


async def seed(count_per_fund: int = 50) -> None:
    async with async_session_factory() as session:
        # Check what already exists
        result = await session.execute(select(Wallet))
        existing_wallets = {w.name: w for w in result.scalars().all()}

        result = await session.execute(select(Fund))
        existing_funds = {(f.wallet_id, f.label): f for f in result.scalars().all()}

        view_key_cipher = ViewKeyEncryption("changeme")

        total_txs = 0

        for i, cfg in enumerate(WALLET_CONFIGS):
            # Create or reuse wallet
            if cfg["name"] in existing_wallets:
                wallet = existing_wallets[cfg["name"]]
                print(f"  Wallet already exists: {wallet.name} ({wallet.id})")
            else:
                # Each wallet gets a unique fake view key
                fake_vk = f"{''.join(chr(ord('a') + (i + j) % 26) for j in range(64))}"
                encrypted_vk = view_key_cipher.encrypt(fake_vk)
                wallet = Wallet(
                    name=cfg["name"],
                    primary_address=cfg["primary_address"],
                    view_key=encrypted_vk,
                    start_height=3_280_000,
                    is_active=True,
                )
                session.add(wallet)
                await session.flush()
                print(f"  Created wallet: {wallet.name} ({wallet.id})")

            # Create funds for this wallet
            for j, fund_cfg in enumerate(cfg["funds"]):
                fund_key = (wallet.id, fund_cfg["label"])
                if fund_key in existing_funds:
                    fund = existing_funds[fund_key]
                    print(f"    Fund already exists: {fund.label} ({fund.id})")
                else:
                    # Generate a unique deterministic deposit address per fund
                    deposit_addr = generate_deposit_address(
                        f"{cfg['name']}-{fund_cfg['label']}"
                    )
                    fund = Fund(
                        wallet_id=wallet.id,
                        label=fund_cfg["label"],
                        description=fund_cfg["description"],
                        deposit_address=deposit_addr,
                        is_active=True,
                        target_amount_xmr=fund_cfg["target_amount_xmr"],
                    )
                    session.add(fund)
                    await session.flush()
                    print(f"    Created fund: {fund.label} ({fund.id})")

                # Generate transactions for this fund
                now = datetime.now(timezone.utc)
                txs: list[Transaction] = []

                for _ in range(count_per_fund):
                    amount_atomic, amount_xmr = random_amount()
                    txs.append(
                        Transaction(
                            fund_id=fund.id,
                            wallet_id=wallet.id,
                            txid=random_txid(),
                            amount_atomic=amount_atomic,
                            amount_xmr=amount_xmr,
                            confirmations=random.randint(1, 1000),
                            timestamp=now
                            - timedelta(
                                days=random.randint(0, 365),
                                hours=random.randint(0, 23),
                                minutes=random.randint(0, 59),
                            ),
                            unlock_time=0,
                            height=random.randint(3_000_000, 3_320_000),
                        )
                    )

                session.add_all(txs)
                total_txs += len(txs)

        await session.commit()
        print(f"\nDone! Total new transactions inserted: {total_txs}")

        # Print summary
        result = await session.execute(select(Wallet))
        all_wallets = result.scalars().all()
        result = await session.execute(select(Fund))
        all_funds = result.scalars().all()

        print("\n--- Summary ---")
        print(f"Wallets: {len(all_wallets)}")
        print(f"Funds:   {len(all_funds)}")
        for w in all_wallets:
            wallet_funds = [f for f in all_funds if f.wallet_id == w.id]
            print(f"  • {w.name}: {len(wallet_funds)} fund(s)")
            for f in wallet_funds:
                print(f"      - {f.label} (target: {f.target_amount_xmr} XMR)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed multi-wallet test data (wallets, funds, transactions)."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of transactions per fund (default: 50)",
    )
    args = parser.parse_args()
    asyncio.run(seed(count_per_fund=args.count))
