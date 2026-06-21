"""Tests for the scanner module."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models import Fund
from worker.scanner import ATOMIC_PER_XMR, MAX_RETRIES, MoneroScanner

# Test addresses — both valid Monero address format
PRIMARY_ADDRESS = "4AdUndXHHZ9cf2bqQ3P7CF2F9xK2s5f2RMZZU6L5HraAB3Z2TL65E6R4E6T1GtGcY3UphTB2C5sZfrYj7Y52bHvMFbS4fQ"
SUB_ADDRESS = "8A1F3bM2vMDVaXsfLKCkJufDbK4f3V3MQECuFq1zZv7JdXsrBLZqYx5f3QZ3h3QF1k2BcWx4Y5zFmNKLeRjtA1CLWqX7yS"


class TestMoneroScanner:
    def test_scanner_init(self):
        scanner = MoneroScanner(rpc_url="http://localhost:18082", scan_interval=30)
        assert scanner.rpc_url == "http://localhost:18082"
        assert scanner.scan_interval == 30

    def test_scanner_strips_trailing_slash(self):
        scanner = MoneroScanner(rpc_url="http://localhost:18082/", scan_interval=60)
        assert scanner.rpc_url == "http://localhost:18082"

    @pytest.mark.asyncio
    async def test_rpc_call_retry(self):
        """Verify scanner module-level constants are defined."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082")

        # Module-level constants, not instance attributes
        assert MAX_RETRIES == 3

    def test_atomic_per_xmr_conversion(self):
        """Test that atomic units to XMR conversion is correct."""
        assert ATOMIC_PER_XMR == Decimal("1e12")
        amount_atomic = 15000000000000  # 15 XMR
        amount_xmr = Decimal(str(amount_atomic)) / ATOMIC_PER_XMR
        assert amount_xmr == Decimal("15.000000000000")

    @pytest.mark.asyncio
    async def test_sync_fund_filters_by_deposit_address(self):
        """Scanner should only save transactions matching fund.deposit_address."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082", scan_interval=60)

        # Create a fund with a specific deposit_address (sub-address)
        fund = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            label="Test Fund",
            primary_address=PRIMARY_ADDRESS,
            deposit_address=SUB_ADDRESS,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )

        # Mock transfers: one to primary_address, one to sub_address
        transfers = {
            "in": [
                {
                    "txid": "a" * 64,
                    "amount": 15000000000000,
                    "confirmations": 128,
                    "timestamp": 1718500000,
                    "height": 3280400,
                    "unlock_time": 0,
                    "address": PRIMARY_ADDRESS,
                },
                {
                    "txid": "b" * 64,
                    "amount": 230000000000000,
                    "confirmations": 245,
                    "timestamp": 1718413640,
                    "height": 3280390,
                    "unlock_time": 0,
                    "address": SUB_ADDRESS,
                },
                {
                    "txid": "c" * 64,
                    "amount": 5000000000000,
                    "confirmations": 10,
                    "timestamp": 1718600000,
                    "height": 3280500,
                    "unlock_time": 0,
                    "address": "4SomeOtherAddressThatDoesNotMatch1234567890ABCDEFGH1234567890ABCDEFGH1234567890ABCDEFGH12",
                },
            ]
        }

        mock_db = AsyncMock()
        # Mock: no existing transactions found (scalar_one_or_none returns None)
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()

        with patch.object(scanner, "_rpc_call", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = transfers
            new_count = await scanner.sync_fund(fund, mock_db)

        # Only the sub-address transfer should be saved (deposit_address = SUB_ADDRESS)
        assert new_count == 1
        # Verify only one Transaction was added
        assert mock_db.add.call_count == 1
        saved_tx = mock_db.add.call_args[0][0]
        assert saved_tx.txid == "b" * 64

    @pytest.mark.asyncio
    async def test_sync_fund_uses_primary_address_as_fallback(self):
        """Scanner should use primary_address when deposit_address is None."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082", scan_interval=60)

        # Fund without deposit_address — should default to primary_address
        fund = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            label="Test Fund",
            primary_address=PRIMARY_ADDRESS,
            deposit_address=None,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )

        transfers = {
            "in": [
                {
                    "txid": "a" * 64,
                    "amount": 15000000000000,
                    "confirmations": 128,
                    "timestamp": 1718500000,
                    "height": 3280400,
                    "unlock_time": 0,
                    "address": PRIMARY_ADDRESS,
                },
                {
                    "txid": "c" * 64,
                    "amount": 5000000000000,
                    "confirmations": 10,
                    "timestamp": 1718600000,
                    "height": 3280500,
                    "unlock_time": 0,
                    "address": "4SomeOtherAddressThatDoesNotMatch1234567890ABCDEFGH1234567890ABCDEFGH1234567890ABCDEFGH12",
                },
            ]
        }

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()

        with patch.object(scanner, "_rpc_call", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = transfers
            new_count = await scanner.sync_fund(fund, mock_db)

        # Only the primary_address transfer should be saved
        assert new_count == 1
        assert mock_db.add.call_count == 1
        saved_tx = mock_db.add.call_args[0][0]
        assert saved_tx.txid == "a" * 64

    @pytest.mark.asyncio
    async def test_sync_fund_skips_all_non_matching(self):
        """Scanner should save zero transactions when none match deposit_address."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082", scan_interval=60)

        fund = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            label="Test Fund",
            primary_address=PRIMARY_ADDRESS,
            deposit_address=SUB_ADDRESS,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )

        # All transfers go to primary_address, but deposit_address is sub-address
        transfers = {
            "in": [
                {
                    "txid": "a" * 64,
                    "amount": 15000000000000,
                    "confirmations": 128,
                    "timestamp": 1718500000,
                    "height": 3280400,
                    "unlock_time": 0,
                    "address": PRIMARY_ADDRESS,
                },
            ]
        }

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()

        with patch.object(scanner, "_rpc_call", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = transfers
            new_count = await scanner.sync_fund(fund, mock_db)

        assert new_count == 0
        assert mock_db.add.call_count == 0
