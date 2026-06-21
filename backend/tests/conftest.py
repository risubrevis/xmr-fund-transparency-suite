"""Test configuration and fixtures."""

import uuid
from unittest.mock import AsyncMock

import pytest
from app.models import Fund, Transaction
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class MockRPCServer:
    """Emulate monero-wallet-rpc responses for tests."""

    PRIMARY_ADDRESS = "4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ"

    TRANSFERS_IN = [
        {
            "txid": "a" * 64,
            "amount": 15000000000000,  # 15 XMR
            "confirmations": 128,
            "timestamp": 1718500000,
            "height": 3280400,
            "unlock_time": 0,
            "address": PRIMARY_ADDRESS,
        },
        {
            "txid": "b" * 64,
            "amount": 230000000000000,  # 230 XMR
            "confirmations": 245,
            "timestamp": 1718413640,
            "height": 3280390,
            "unlock_time": 0,
            "address": PRIMARY_ADDRESS,
        },
    ]

    async def get_transfers(self, params: dict = None) -> dict:
        return {"in": self.TRANSFERS_IN}

    async def generate_from_keys(self, params: dict = None) -> dict:
        return {"result": "ok"}


@pytest.fixture
def mock_rpc():
    return MockRPCServer()


@pytest.fixture
def mock_rpc_call(mock_rpc):
    async def _rpc_call(method: str, params: dict = None):
        handler = getattr(mock_rpc, method, None)
        if handler:
            return await handler(params)
        raise RuntimeError(f"Unknown method: {method}")

    return _rpc_call


@pytest.fixture
def sample_fund_data():
    """Sample fund data for creating a test fund."""
    return {
        "label": "Test Fund",
        "primary_address": "4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ",
        "view_key": "a" * 64,
        "start_height": 3280000,
    }
