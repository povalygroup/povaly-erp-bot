"""Manually run migration 004 to add issue_ticket column."""

import asyncio
import logging
from src.data.adapters.factory import create_database_adapter
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run migration 004."""
    logger.info("Starting migration 004...")
    
    # Load config from environment
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    config = Config(
        TELEGRAM_BOT_TOKEN=os.getenv('TELEGRAM_BOT_TOKEN'),
        TELEGRAM_GROUP_ID=int(os.getenv('TELEGRAM_GROUP_ID'))
    )
    
    # Create database adapter
    db_adapter = create_database_adapter(config)
    await db_adapter.initialize()
    
    try:
        # Add issue_ticket column
        await db_adapter.execute_query(
            "ALTER TABLE issues ADD COLUMN issue_ticket TEXT"
        )
        logger.info("✅ Added issue_ticket column to issues table")
        
        # Update existing issues to have issue_ticket = ticket-I1
        await db_adapter.execute_query(
            "UPDATE issues SET issue_ticket = ticket || '-I1' WHERE issue_ticket IS NULL"
        )
        logger.info("✅ Updated existing issues with issue_ticket values")
        
        # Record migration
        from datetime import datetime
        await db_adapter.conn.execute(
            "INSERT INTO migrations (name, applied_at) VALUES (?, ?)",
            ("migration_004_add_issue_ticket", datetime.now().isoformat())
        )
        await db_adapter.conn.commit()
        logger.info("✅ Migration 004 recorded in database")
        
        logger.info("✅ Migration 004 completed successfully!")
        
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            logger.info("ℹ️ Column already exists, skipping...")
        else:
            logger.error(f"❌ Migration failed: {e}")
            raise
    finally:
        # Close database connection
        if hasattr(db_adapter, 'conn'):
            await db_adapter.conn.close()


if __name__ == "__main__":
    asyncio.run(main())
