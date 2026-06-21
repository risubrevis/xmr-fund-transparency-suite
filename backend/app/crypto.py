import re

from cryptography.fernet import Fernet
from fastapi import HTTPException


class ViewKeyEncryption:
    """AES-256 encryption for view keys stored in database."""

    def __init__(self, master_secret: str):
        import base64
        import hashlib

        # Derive a valid Fernet key from the master secret
        key = hashlib.sha256(master_secret.encode()).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(key))

    def encrypt(self, view_key: str) -> str:
        return self.cipher.encrypt(view_key.encode()).decode()

    def decrypt(self, encrypted_view_key: str) -> str:
        return self.cipher.decrypt(encrypted_view_key.encode()).decode()


def validate_monero_address(address: str) -> bool:
    """Validate Monero address (4/8/AB prefix, base58, 95 chars)."""
    return bool(re.match(r"^[48AB][1-9A-HJ-NP-Za-km-z]{94}$", address))


def validate_view_key(view_key: str) -> bool:
    """Validate private view key (64 hex characters)."""
    return bool(re.match(r"^[0-9a-fA-F]{64}$", view_key))


def validate_fund_input(
    address: str, view_key: str, deposit_address: str | None = None
) -> None:
    """Validate fund input data, raise HTTPException on error."""
    if not validate_monero_address(address):
        raise HTTPException(
            status_code=400,
            detail="Invalid Monero address. Must be 95 characters, base58, starting with 4/8/A/B.",
        )
    if deposit_address is not None and not validate_monero_address(deposit_address):
        raise HTTPException(
            status_code=400,
            detail="Invalid Monero deposit address. Must be 95 characters, base58, starting with 4/8/A/B.",
        )
    if not validate_view_key(view_key):
        raise HTTPException(
            status_code=400,
            detail="Invalid view key. Must be 64 hexadecimal characters.",
        )
