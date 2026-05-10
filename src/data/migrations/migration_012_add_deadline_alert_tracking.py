"""Migration 012: Add deadline alert tracking to tasks table."""

import logging

logger = logging.getLogger(__name__)


async def upgrade(db_adapter):
    """Add last_overdue_alert_date field to tasks table."""
    try:
        # Add last_overdue_alert_date column to tasks table
        await db_adapter.conn.execute("""
            ALTER TABLE tasks ADD COLUMN last_overdue_alert_date TEXT
        """)
        await db_adapter.conn.commit()
        
        logger.info("✅ Added last_overdue_alert_date column to tasks table")
        return True
        
    except Exception as e:
        # Column might already exist
        if "duplicate column name" in str(e).lower():
            logger.info("⚠️ Column last_overdue_alert_date already exists")
            return True
        logger.error(f"❌ Migration 012 failed: {e}")
        return False


async def downgrade(db_adapter):
    """Remove last_overdue_alert_date field from tasks table."""
    try:
        # SQLite doesn't support DROP COLUMN directly, would need table recreation
        logger.warning("⚠️ Downgrade not implemented for migration 012")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 012 downgrade failed: {e}")
        return False
