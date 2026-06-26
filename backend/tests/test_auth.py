"""Tests for authentication module."""

from unittest.mock import patch

import pytest
from app.auth import verify_api_key
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_verify_api_key_valid():
    """Test that a valid API key passes verification."""
    from app.config import Settings

    test_settings = Settings(api_key="test-api-key-12345")
    with patch("app.auth.settings", test_settings):
        result = await verify_api_key(x_api_key="test-api-key-12345")
    assert result == "test-api-key-12345"


@pytest.mark.asyncio
async def test_verify_api_key_invalid():
    """Test that an invalid API key raises 401."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(x_api_key="wrong-key")
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail
