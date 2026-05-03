"""Migration 010: Add deadline column to tasks table."""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db):
    """Add deadline column to tasks table."""
    try:
        logger.info("Running migration 010: Adding deadline column to tasks table")
        
        # Add deadline column (nullable datetime)
        await db.conn.execute("""
            ALTER TABLE tasks ADD COLUMN deadline TEXT
        """)
        await db.conn.commit()
        
        logger.info("✅ Migration 010 completed: deadline column added")
        
    except Exception as e:
        logger.error(f"❌ Migration 010 failed: {e}")
        raise


async def migrate_down(db):
    """Remove deadline column from tasks table."""
    try:
        logger.info("Running migration 010 downgrade: Removing deadline column")
        
        # SQLite doesn't support DROP COLUMN directly, need to recreate table
        # For now, just log that downgrade is not supported
        logger.warning("⚠️ Downgrade not supported for SQLite ALTER TABLE ADD COLUMN")
        logger.warning("   To remove column, you would need to recreate the entire table")
        
    except Exception as e:
        logger.error(f"❌ Migration 010 downgrade failed: {e}")
        raise
