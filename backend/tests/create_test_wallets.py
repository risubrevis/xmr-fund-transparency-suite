"""Seed multiple test wallets and funds for multi-wallet testing.

Creates additional wallets and funds if they don't already exist,
so that the scanner and API can be tested with multiple wallets.

Usage:
    python -m tests.create_test_wallets
"""

import asyncio
from decimal import Decimal

from app.config import settings
from app.crypto import ViewKeyEncryption
from app.database import async_session_factory
from app.models import Fund, Wallet
from sqlalchemy import select

# Test wallets data — each uses a unique 95-char Monero address
# and a unique 64-hex-char view key (fake but valid format)
TEST_WALLETS = [
    {
        "name": "Community Chest Donation Wallet",
        # Subaddress starting with '8'
        "primary_address": "8MLtiKEpF3XQFZSwQyMQAkj2egqiwNhU5tf8uN4c4Gr4mzZSLvgAcpBBzvu687HZQo9EUJEwMZAvnsJh2FoDPykU8ZfPvcu",
        "view_key": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "start_height": 3_280_000,
        "funds": [
            {
                "label": "Community General Fund",
                "deposit_address": "8mPuyYUZtnNLkGdUr1redj6qpSE6KQKMPaXjJ4avgG2EXsTyeppmUfaonFdhRpcrQofNkqwAjvZqLickZHG5RmSbEvtDEwH",
                "target_amount_xmr": Decimal("500"),
            },
            {
                "label": "Community Infrastructure Fund",
                "deposit_address": "8s1cWvLfEUC6iw3oL9UnTu5qmzC67sWcAYU5FvYdPkH26uV5R3mJg16WcDp2QW8HrrQTWM4G1K4dVgcPcvDUcaeRTDTtd5C",
                "target_amount_xmr": Decimal("250"),
            },
        ],
    },
    {
        "name": "Developer Fund Wallet",
        # Standard address starting with '4'
        "primary_address": "4Fqm2HqwDPs1ov4L2MVf1E38stWqhBPC7ZvHbU4BZqEvniNyhnj7vX5SfkfoDsP2Gi3hzQtpA6gi6DbyqiYV8YYmsNB7E3a",
        "view_key": "b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2",
        "start_height": 3_280_000,
        "funds": [
            {
                "label": "Dev Bounty Fund",
                "deposit_address": "4Fqm2HqwDPs1ov4L2MVf1E38stWqhBPC7ZvHbU4BZqEvniNyhnj7vX5SfkfoDsP2Gi3hzQtpA6gi6DbyqiYV8YYmsNB7E3a",
                "target_amount_xmr": Decimal("100"),
            },
        ],
    },
]


async def seed() -> None:
    """Create test wallets and funds if they don't exist."""
    cipher = ViewKeyEncryption(settings.view_key_master_secret)

    async with async_session_factory() as session:
        existing = (await session.execute(select(Wallet))).scalars().all()
        print(f"Found {len(existing)} existing wallet(s)")

        for wallet_data in TEST_WALLETS:
            # Check if wallet with this name already exists
            result = await session.execute(
                select(Wallet).where(Wallet.name == wallet_data["name"])
            )
            existing_wallet = result.scalar_one_or_none()
            if existing_wallet:
                print(
                    f"Wallet '{wallet_data['name']}' already exists "
                    f"(id={existing_wallet.id}), skipping"
                )
                continue

            # Create wallet with encrypted view key
            encrypted_view_key = cipher.encrypt(wallet_data["view_key"])
            wallet = Wallet(
                name=wallet_data["name"],
                primary_address=wallet_data["primary_address"],
                view_key=encrypted_view_key,
                start_height=wallet_data["start_height"],
                is_active=True,
            )
            session.add(wallet)
            await session.flush()

            print(
                f"Created wallet: '{wallet.name}' "
                f"(id={wallet.id}, uuid={wallet.uuid})"
            )

            # Create funds for this wallet
            for fund_data in wallet_data["funds"]:
                fund = Fund(
                    wallet_id=wallet.id,
                    label=fund_data["label"],
                    deposit_address=fund_data["deposit_address"],
                    is_active=True,
                    target_amount_xmr=fund_data["target_amount_xmr"],
                )
                session.add(fund)
                print(
                    f"  Created fund: '{fund.label}' "
                    f"(deposit={fund.deposit_address[:20]}...)"
                )

            await session.commit()

        # Summary
        wallets = (await session.execute(select(Wallet))).scalars().all()
        funds = (await session.execute(select(Fund))).scalars().all()
        print(f"\nTotal wallets: {len(wallets)}")
        print(f"Total funds: {len(funds)}")
        for w in wallets:
            print(f"  Wallet: {w.name} (uuid={w.uuid}, active={w.is_active})")
            wallet_funds = [f for f in funds if f.wallet_id == w.id]
            for f in wallet_funds:
                print(f"    Fund: {f.label}")


if __name__ == "__main__":
    asyncio.run(seed())
