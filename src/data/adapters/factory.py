# Copy this entire content to: src/data/adapters/factory.py

"""Database adapter factory."""

from src.config import Config
from .sqlite_adapter import SQLiteAdapter


def create_database_adapter(config: Config):
    """Create database adapter based on configuration."""
    if config.DATABASE_TYPE == "sqlite":
        return SQLiteAdapter(config.DATABASE_PATH)
    elif config.DATABASE_TYPE == "mongodb":
        raise NotImplementedError("MongoDB adapter not yet implemented")
    elif config.DATABASE_TYPE == "json":
        raise NotImplementedError("JSON adapter not yet implemented")
    else:
        raise ValueError(f"Unsupported database type: {config.DATABASE_TYPE}")

