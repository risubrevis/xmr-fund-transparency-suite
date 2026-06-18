"""Seed a test fund into the database.

Creates a fund with predefined test data if one doesn't already exist.
Prints the fund UUID to stdout for use by other scripts.
"""

import asyncio
from decimal import Decimal

from app.database import async_session_factory
from app.models import Fund
from sqlalchemy import select

TEST_FUND_LABEL = "Test Fund"
TEST_TARGET_XMR = Decimal("1000")


async def seed() -> None:
    async with async_session_factory() as session:
        # Reuse any existing fund — avoid duplicates on repeated runs
        result = await session.execute(select(Fund).limit(1))
        fund = result.scalar_one_or_none()

        if fund:
            print(fund.id)
            return

        fund = Fund(
            label=TEST_FUND_LABEL,
            primary_address="4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ",
            view_key="a" * 64,
            start_height=3_280_000,
            is_active=True,
            target_amount_xmr=TEST_TARGET_XMR,
        )
        session.add(fund)
        await session.commit()
        await session.refresh(fund)
        print(fund.id)


if __name__ == "__main__":
    asyncio.run(seed())
