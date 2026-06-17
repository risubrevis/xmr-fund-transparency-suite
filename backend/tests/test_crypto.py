"""Tests for crypto module (view key validation and encryption)."""

import pytest
from app.crypto import ViewKeyEncryption, validate_monero_address, validate_view_key


class TestViewKeyValidation:
    def test_valid_view_key(self):
        assert validate_view_key("a" * 64) is True
        assert validate_view_key("abcdef1234567890" * 4) is True

    def test_invalid_view_key_too_short(self):
        assert validate_view_key("abc123") is False

    def test_invalid_view_key_non_hex(self):
        assert validate_view_key("g" * 64) is False

    def test_invalid_view_key_empty(self):
        assert validate_view_key("") is False


class TestMoneroAddressValidation:
    def test_valid_address_starts_with_4(self):
        # This is a valid format but may not be a real address
        addr = "4" + "1" * 94
        assert validate_monero_address(addr) is True

    def test_valid_address_starts_with_8(self):
        addr = "8" + "1" * 94
        assert validate_monero_address(addr) is True

    def test_invalid_address_wrong_prefix(self):
        addr = "5" + "1" * 94
        assert validate_monero_address(addr) is False

    def test_invalid_address_too_short(self):
        assert validate_monero_address("4" + "1" * 50) is False


class TestViewKeyEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        cipher = ViewKeyEncryption("my-secret-key-12345")
        original = "a" * 64
        encrypted = cipher.encrypt(original)
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_output(self):
        cipher = ViewKeyEncryption("my-secret-key-12345")
        original = "a" * 64
        encrypted = cipher.encrypt(original)
        assert encrypted != original

    def test_decrypt_with_wrong_key_fails(self):
        cipher1 = ViewKeyEncryption("key-one")
        cipher2 = ViewKeyEncryption("key-two")
        encrypted = cipher1.encrypt("a" * 64)
        with pytest.raises(Exception):
            cipher2.decrypt(encrypted)
