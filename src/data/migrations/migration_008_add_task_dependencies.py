"""Migration 008: Add task dependencies support."""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db_adapter):
    """Apply migration - add task dependencies table."""
    try:
        # Create task_dependencies table
        await db_adapter.execute("""
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket TEXT NOT NULL,
                blocked_by_ticket TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                created_by INTEGER NOT NULL,
                FOREIGN KEY (ticket) REFERENCES tasks(ticket),
                FOREIGN KEY (blocked_by_ticket) REFERENCES tasks(ticket),
                UNIQUE(ticket, blocked_by_ticket)
            )
        """)
        
        # Create indexes
        await db_adapter.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_dependencies_ticket 
            ON task_dependencies(ticket)
        """)
        
        await db_adapter.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_dependencies_blocked_by 
            ON task_dependencies(blocked_by_ticket)
        """)
        
        logger.info("✅ Migration 008: task_dependencies table created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 008 failed: {e}")
        return False


async def migrate_down(db_adapter):
    """Rollback migration - drop task_dependencies table."""
    try:
        await db_adapter.execute("DROP TABLE IF EXISTS task_dependencies")
        logger.info("✅ Migration 008 rollback: task_dependencies table dropped")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 008 rollback failed: {e}")
        return False
