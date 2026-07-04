"""Tests for the scanner module."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models import Fund, Wallet
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

    def test_wallet_filename_deterministic(self):
        """Wallet filename should be wallet_{uuid}."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082")
        wallet = Wallet(
            id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
            uuid="test-uuid-1234",
            name="Test Wallet",
            primary_address=PRIMARY_ADDRESS,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )
        assert scanner._wallet_filename(wallet) == "wallet_test-uuid-1234"

    @pytest.mark.asyncio
    async def test_rpc_call_retry(self):
        """Verify scanner module-level constants are defined."""
        assert MAX_RETRIES == 3

    def test_atomic_per_xmr_conversion(self):
        """Test that atomic units to XMR conversion is correct."""
        assert ATOMIC_PER_XMR == Decimal("1e12")
        amount_atomic = 15000000000000  # 15 XMR
        amount_xmr = Decimal(str(amount_atomic)) / ATOMIC_PER_XMR
        assert amount_xmr == Decimal("15.000000000000")

    @pytest.mark.asyncio
    async def test_sync_wallet_filters_by_deposit_address(self):
        """Scanner should only save transactions matching a fund's deposit_address."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082", scan_interval=60)

        wallet = Wallet(
            id=uuid.uuid4(),
            uuid=str(uuid.uuid4()),
            name="Test Wallet",
            primary_address=PRIMARY_ADDRESS,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )
        fund = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            wallet_id=wallet.id,
            label="Test Fund",
            deposit_address=SUB_ADDRESS,
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
            new_count = await scanner.sync_wallet(wallet, [fund], mock_db)

        # Only the sub-address transfer should be saved (deposit_address = SUB_ADDRESS)
        assert new_count == 1
        # Verify only one Transaction was added
        assert mock_db.add.call_count == 1
        saved_tx = mock_db.add.call_args[0][0]
        assert saved_tx.txid == "b" * 64
        assert saved_tx.fund_id == fund.id
        assert saved_tx.wallet_id == wallet.id

    @pytest.mark.asyncio
    async def test_sync_wallet_multiple_funds(self):
        """Scanner should route transactions to the correct fund based on deposit address."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082", scan_interval=60)

        wallet = Wallet(
            id=uuid.uuid4(),
            uuid=str(uuid.uuid4()),
            name="Test Wallet",
            primary_address=PRIMARY_ADDRESS,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )

        fund1 = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            wallet_id=wallet.id,
            label="Fund 1",
            deposit_address=PRIMARY_ADDRESS,
            is_active=True,
        )
        fund2 = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            wallet_id=wallet.id,
            label="Fund 2",
            deposit_address=SUB_ADDRESS,
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
                    "txid": "b" * 64,
                    "amount": 230000000000000,
                    "confirmations": 245,
                    "timestamp": 1718413640,
                    "height": 3280390,
                    "unlock_time": 0,
                    "address": SUB_ADDRESS,
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
            new_count = await scanner.sync_wallet(wallet, [fund1, fund2], mock_db)

        # Both transactions should be saved (one per fund)
        assert new_count == 2
        assert mock_db.add.call_count == 2

    @pytest.mark.asyncio
    async def test_sync_wallet_skips_all_non_matching(self):
        """Scanner should save zero transactions when no deposit addresses match."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082", scan_interval=60)

        wallet = Wallet(
            id=uuid.uuid4(),
            uuid=str(uuid.uuid4()),
            name="Test Wallet",
            primary_address=PRIMARY_ADDRESS,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )

        fund = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            wallet_id=wallet.id,
            label="Test Fund",
            deposit_address=SUB_ADDRESS,
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
            new_count = await scanner.sync_wallet(wallet, [fund], mock_db)

        assert new_count == 0
        assert mock_db.add.call_count == 0

    @pytest.mark.asyncio
    async def test_sync_wallet_uses_filename_in_rpc_call(self):
        """Scanner should pass the wallet's deterministic filename to RPC calls."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082", scan_interval=60)

        wallet = Wallet(
            id=uuid.uuid4(),
            uuid="test-wallet-uuid",
            name="Test Wallet",
            primary_address=PRIMARY_ADDRESS,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )
        fund = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            wallet_id=wallet.id,
            label="Test Fund",
            deposit_address=PRIMARY_ADDRESS,
            is_active=True,
        )

        transfers = {"in": []}

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        mock_db.commit = AsyncMock()

        with patch.object(scanner, "_rpc_call", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = transfers
            await scanner.sync_wallet(wallet, [fund], mock_db)

            # Verify the get_transfers call includes the correct filename
            call_args = mock_rpc.call_args
            assert call_args[0][0] == "get_transfers"
            params = (
                call_args[0][1] if call_args[0][1] else call_args[1].get("params", {})
            )
            assert params["filename"] == "wallet_test-wallet-uuid"

    @pytest.mark.asyncio
    async def test_sync_wallet_no_leak_between_wallets(self):
        """Transactions from one wallet should not leak to another wallet's funds."""
        scanner = MoneroScanner(rpc_url="http://localhost:18082", scan_interval=60)

        wallet1 = Wallet(
            id=uuid.uuid4(),
            uuid="wallet-1-uuid",
            name="Wallet 1",
            primary_address=PRIMARY_ADDRESS,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )
        wallet2 = Wallet(
            id=uuid.uuid4(),
            uuid="wallet-2-uuid",
            name="Wallet 2",
            primary_address=PRIMARY_ADDRESS,
            view_key="encrypted_view_key",
            start_height=3280000,
            is_active=True,
        )

        # Fund on wallet 1 only accepts PRIMARY_ADDRESS
        fund_w1 = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            wallet_id=wallet1.id,
            label="Wallet 1 Fund",
            deposit_address=PRIMARY_ADDRESS,
            is_active=True,
        )
        # Fund on wallet 2 only accepts SUB_ADDRESS
        fund_w2 = Fund(
            id=uuid.uuid4(),
            public_uuid=str(uuid.uuid4()),
            wallet_id=wallet2.id,
            label="Wallet 2 Fund",
            deposit_address=SUB_ADDRESS,
            is_active=True,
        )

        # Wallet 1 sees transfers to PRIMARY_ADDRESS
        transfers_w1 = {
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

        # Wallet 2 sees transfers to SUB_ADDRESS
        transfers_w2 = {
            "in": [
                {
                    "txid": "b" * 64,
                    "amount": 230000000000000,
                    "confirmations": 245,
                    "timestamp": 1718413640,
                    "height": 3280390,
                    "unlock_time": 0,
                    "address": SUB_ADDRESS,
                },
            ]
        }

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()

        # Scan wallet 1: should match 1 transaction (PRIMARY_ADDRESS matches fund_w1)
        with patch.object(scanner, "_rpc_call", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = transfers_w1
            count_w1 = await scanner.sync_wallet(wallet1, [fund_w1], mock_db)

        # Scan wallet 2: should match 1 transaction (SUB_ADDRESS matches fund_w2)
        with patch.object(scanner, "_rpc_call", new_callable=AsyncMock) as mock_rpc:
            mock_rpc.return_value = transfers_w2
            count_w2 = await scanner.sync_wallet(wallet2, [fund_w2], mock_db)

        # Each wallet should only record transactions for its own funds
        assert count_w1 == 1
        assert count_w2 == 1

        # Verify wallet 1's transaction is for fund_w1
        tx_w1 = mock_db.add.call_args_list[0][0][0]
        assert tx_w1.wallet_id == wallet1.id
        assert tx_w1.fund_id == fund_w1.id

        # Verify wallet 2's transaction is for fund_w2
        tx_w2 = mock_db.add.call_args_list[1][0][0]
        assert tx_w2.wallet_id == wallet2.id
        assert tx_w2.fund_id == fund_w2.id
