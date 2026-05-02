"""Pytest configuration and fixtures."""

import pytest
from src.config import Config


@pytest.fixture
def test_config():
    """Create test configuration."""
    return Config(
        TELEGRAM_BOT_TOKEN="test_token",
        TELEGRAM_GROUP_ID=-1001234567890,
        DATABASE_TYPE="sqlite",
        DATABASE_PATH=":memory:",
        DATABASE_ENCRYPTION_KEY="test_key_32_characters_long!!!",
        BRAND_CODES=["PV", "VB"],
        ADMINISTRATORS=[123456789],
    )
