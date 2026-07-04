"""Test configuration and fixtures."""

import pytest


class MockRPCServer:
    """Emulate monero-wallet-rpc responses for tests.

    Supports multi-wallet mode by tracking open wallets by filename
    and validating filename parameters in requests.
    """

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

    def __init__(self):
        # Track which wallets are "open" in multi-wallet mode
        self.open_wallets: set[str] = set()
        self.registered_wallets: set[str] = set()

    async def get_transfers(self, params: dict = None) -> dict:
        """Return incoming transfers, validating filename is present."""
        params = params or {}
        filename = params.get("filename")
        # In multi-wallet mode, filename must be provided
        if filename and filename not in self.open_wallets:
            # Auto-open for test purposes
            self.open_wallets.add(filename)
        return {"in": self.TRANSFERS_IN}

    async def generate_from_keys(self, params: dict = None) -> dict:
        """Register a view-only wallet, tracking by filename."""
        params = params or {}
        filename = params.get("filename", "viewonly")
        self.registered_wallets.add(filename)
        self.open_wallets.add(filename)
        return {"result": "ok"}

    async def open_wallet(self, params: dict = None) -> dict:
        """Open a wallet by filename."""
        params = params or {}
        filename = params.get("filename", "viewonly")
        if filename in self.registered_wallets or filename in self.open_wallets:
            self.open_wallets.add(filename)
            return {"result": "ok"}
        # Simulate "wallet not found" error
        raise RuntimeError(f"Wallet not found: {filename}")

    async def close_wallet(self, params: dict = None) -> dict:
        """Close a wallet by filename."""
        params = params or {}
        filename = params.get("filename")
        if filename:
            self.open_wallets.discard(filename)
        else:
            # Close whichever wallet is currently active
            self.open_wallets.clear()
        return {}

    async def get_height(self, params: dict = None) -> dict:
        """Return a mock block height."""
        return {"height": 3280500}

    async def get_balance(self, params: dict = None) -> dict:
        """Return a mock balance."""
        return {"balance": 0, "unlocked_balance": 0}


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
def sample_wallet_data():
    """Sample wallet data for creating a test wallet."""
    return {
        "name": "Test Wallet",
        "primary_address": "4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ",
        "view_key": "a" * 64,
        "start_height": 3280000,
    }


@pytest.fixture
def sample_fund_data():
    """Sample fund data for creating a test fund (requires existing wallet)."""
    return {
        "label": "Test Fund",
        "deposit_address": "4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ",
    }
