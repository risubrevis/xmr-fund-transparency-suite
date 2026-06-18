"""Seed random transactions for existing funds.

Usage:
    python -m tests.create_test_transactions --count=50 [--fund-id=UUID]

If --fund-id is omitted, the first fund in the database is used.
Transactions are always appended — existing data is never deleted.
"""

import argparse
import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.database import async_session_factory
from app.models import Fund, Transaction
from sqlalchemy import select

PICONERO = Decimal("1e12")


def random_txid() -> str:
    """Generate a random 64-character hex transaction ID."""
    return uuid.uuid4().hex + uuid.uuid4().hex


async def seed(count: int, fund_id: str | None = None) -> None:
    async with async_session_factory() as session:
        if fund_id:
            result = await session.execute(
                select(Fund).where(Fund.id == uuid.UUID(fund_id))
            )
            fund = result.scalar_one_or_none()
            if not fund:
                print(
                    f"ERROR: Fund with id {fund_id} not found.",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            result = await session.execute(select(Fund).limit(1))
            fund = result.scalar_one_or_none()

        if not fund:
            print(
                "ERROR: No funds found in database. Run seed_test_data.py first.",
                file=sys.stderr,
            )
            sys.exit(1)

        now = datetime.now(timezone.utc)
        transactions = []

        for _ in range(count):
            # 0.01 XMR to ~500 XMR in atomic units
            amount_atomic = random.randint(10_000_000_000, 500_000_000_000_000)
            amount_xmr = Decimal(amount_atomic) / PICONERO

            transactions.append(
                Transaction(
                    fund_id=fund.id,
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

        session.add_all(transactions)
        await session.commit()
        print(f"Inserted {count} transactions for fund '{fund.label}' ({fund.id})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed random transactions for a fund.")
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of transactions to generate (default: 50)",
    )
    parser.add_argument(
        "--fund-id",
        type=str,
        default=None,
        help="Fund UUID (uses first fund if omitted)",
    )
    args = parser.parse_args()
    asyncio.run(seed(args.count, args.fund_id))
