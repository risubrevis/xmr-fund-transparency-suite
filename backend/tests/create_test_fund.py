"""Seed a test wallet and fund into the database.

Creates a wallet and fund with predefined test data if they don't already exist.
Prints the wallet and fund UUIDs to stdout for use by other scripts.
"""

import asyncio
from decimal import Decimal

from app.crypto import ViewKeyEncryption
from app.database import async_session_factory
from app.models import Fund, Wallet
from sqlalchemy import select

TEST_WALLET_NAME = "Test Wallet"
TEST_FUND_LABEL = "Test Fund"
TEST_TARGET_XMR = Decimal("1000")
TEST_ADDRESS = "4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ"


async def seed() -> None:
    async with async_session_factory() as session:
        # Reuse any existing wallet — avoid duplicates on repeated runs
        result = await session.execute(select(Wallet).limit(1))
        wallet = result.scalar_one_or_none()

        if wallet:
            print(f"Wallet already exists: {wallet.id}")

            # Reuse any existing fund
            result = await session.execute(select(Fund).limit(1))
            fund = result.scalar_one_or_none()
            if fund:
                # Backfill target_amount_xmr for funds created before migration
                if fund.target_amount_xmr is None:
                    fund.target_amount_xmr = TEST_TARGET_XMR
                    await session.commit()
                print(fund.id)
            else:
                # Create a fund for the existing wallet
                fund = Fund(
                    wallet_id=wallet.id,
                    label=TEST_FUND_LABEL,
                    deposit_address=wallet.primary_address,
                    is_active=True,
                    target_amount_xmr=TEST_TARGET_XMR,
                )
                session.add(fund)
                await session.commit()
                await session.refresh(fund)
                print(fund.id)
            return

        # Create a new wallet with encrypted view key
        cipher = ViewKeyEncryption("changeme")
        encrypted_view_key = cipher.encrypt("a" * 64)

        wallet = Wallet(
            name=TEST_WALLET_NAME,
            primary_address=TEST_ADDRESS,
            view_key=encrypted_view_key,
            start_height=3_280_000,
            is_active=True,
        )
        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)

        # Create a default fund for the wallet
        fund = Fund(
            wallet_id=wallet.id,
            label=TEST_FUND_LABEL,
            deposit_address=wallet.primary_address,
            is_active=True,
            target_amount_xmr=TEST_TARGET_XMR,
        )
        session.add(fund)
        await session.commit()
        await session.refresh(fund)

        print(f"Created wallet: {wallet.id}")
        print(f"Created fund: {fund.id}")


if __name__ == "__main__":
    asyncio.run(seed())
