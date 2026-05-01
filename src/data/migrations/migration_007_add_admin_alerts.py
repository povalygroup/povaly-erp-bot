"""Migration 007: Add admin_alerts table for tracking Admin Control Panel messages."""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db_adapter):
    """Apply migration - create admin_alerts table."""
    try:
        # Create admin_alerts table
        await db_adapter.execute("""
            CREATE TABLE IF NOT EXISTS admin_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL UNIQUE,
                topic_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                alert_content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                resolved INTEGER DEFAULT 0,
                acknowledged_at TIMESTAMP,
                resolved_at TIMESTAMP,
                acknowledged_by INTEGER,
                resolved_by INTEGER
            )
        """)
        
        # Create indexes
        await db_adapter.execute("""
            CREATE INDEX IF NOT EXISTS idx_admin_alerts_message_id 
            ON admin_alerts(message_id)
        """)
        
        await db_adapter.execute("""
            CREATE INDEX IF NOT EXISTS idx_admin_alerts_resolved 
            ON admin_alerts(resolved)
        """)
        
        await db_adapter.execute("""
            CREATE INDEX IF NOT EXISTS idx_admin_alerts_created_at 
            ON admin_alerts(created_at)
        """)
        
        logger.info("✅ Migration 007: admin_alerts table created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 007 failed: {e}")
        return False


async def migrate_down(db_adapter):
    """Rollback migration - drop admin_alerts table."""
    try:
        await db_adapter.execute("DROP TABLE IF EXISTS admin_alerts")
        logger.info("✅ Migration 007 rollback: admin_alerts table dropped")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 007 rollback failed: {e}")
        return False
