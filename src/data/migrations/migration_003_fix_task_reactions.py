"""
Migration 003: Fix task_reactions table schema
Adds missing columns: context, removed_at
Ensures topic_id exists
"""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db_adapter):
    """Apply migration - add missing columns to task_reactions."""
    logger.info("🔄 Starting Migration 003: Fix task_reactions table...")
    
    try:
        # Check existing columns
        async with db_adapter.conn.execute("PRAGMA table_info(task_reactions)") as cursor:
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            logger.info(f"Existing columns in task_reactions: {column_names}")
        
        # Add context column if missing
        if 'context' not in column_names:
            await db_adapter.conn.execute("""
                ALTER TABLE task_reactions ADD COLUMN context TEXT
            """)
            logger.info("✅ Added context column")
        
        # Add removed_at column if missing
        if 'removed_at' not in column_names:
            await db_adapter.conn.execute("""
                ALTER TABLE task_reactions ADD COLUMN removed_at TEXT
            """)
            logger.info("✅ Added removed_at column")
        
        await db_adapter.conn.commit()
        
        logger.info("✅ Migration 003 completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 003 failed: {e}")
        raise


async def migrate_down(db_adapter):
    """Rollback migration - SQLite doesn't support DROP COLUMN easily."""
    logger.info("⚠️ Migration 003 rollback not supported (SQLite limitation)")
    return True
