"""Migration 006: Add break_records table for attendance break tracking."""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db_adapter):
    """Add break_records table."""
    try:
        logger.info("Running migration 006: Add break_records table")
        
        # Create break_records table
        await db_adapter.execute_query("""
            CREATE TABLE IF NOT EXISTS break_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                break_start TEXT NOT NULL,
                break_end TEXT,
                reason TEXT NOT NULL,
                duration_minutes REAL,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # Create index for performance
        await db_adapter.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_break_records_user_date 
            ON break_records(user_id, date)
        """)
        
        logger.info("✅ Migration 006 completed: break_records table created")
        return True
    except Exception as e:
        logger.error(f"Migration 006 failed: {e}")
        raise


async def migrate_down(db_adapter):
    """Remove break_records table."""
    try:
        logger.info("Rolling back migration 006: Remove break_records table")
        
        await db_adapter.execute_query("DROP TABLE IF EXISTS break_records")
        await db_adapter.execute_query("DROP INDEX IF EXISTS idx_break_records_user_date")
        
        logger.info("✅ Migration 006 rolled back")
        return True
    except Exception as e:
        logger.error(f"Migration 006 rollback failed: {e}")
        raise
