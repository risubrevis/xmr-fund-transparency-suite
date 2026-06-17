"""Tests for authentication module."""

import pytest
from app.auth import verify_api_key
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_verify_api_key_valid():
    """Test that a valid API key passes verification."""
    import os

    original = os.environ.get("API_KEY")
    os.environ["API_KEY"] = "test-api-key-12345"

    # Reload settings to pick up the env var
    from app.config import Settings

    settings = Settings(api_key="test-api-key-12345")

    result = await verify_api_key(x_api_key="test-api-key-12345")
    assert result == "test-api-key-12345"


@pytest.mark.asyncio
async def test_verify_api_key_invalid():
    """Test that an invalid API key raises 401."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(x_api_key="wrong-key")
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail
