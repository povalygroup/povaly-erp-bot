"""Migration 005: Fix issue table constraints - allow multiple issues per task."""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db_adapter):
    """Fix issue table constraints."""
    try:
        # SQLite doesn't support modifying constraints directly
        # We need to recreate the table
        
        # 0. Drop any views that depend on issues table
        await db_adapter.conn.execute("DROP VIEW IF EXISTS v_ticket_status")
        await db_adapter.conn.execute("DROP VIEW IF EXISTS v_issue_status")
        logger.info("Dropped views that depend on issues table")
        
        # 1. Create new table with correct constraints (no id column, issue_ticket is unique)
        await db_adapter.conn.execute("""
            CREATE TABLE IF NOT EXISTS issues_new (
                ticket TEXT NOT NULL,
                issue_ticket TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                details TEXT NOT NULL,
                priority TEXT NOT NULL,
                assignee_username TEXT,
                creator_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT,
                claimed_at TEXT,
                resolved_at TEXT,
                escalated_at TEXT,
                claimed_by TEXT,
                resolved_by INTEGER,
                rejected_by INTEGER,
                escalation_sent INTEGER DEFAULT 0,
                reminder_sent INTEGER DEFAULT 0
            )
        """)
        logger.info("Created new issues table with correct constraints")
        
        # 2. Copy data from old table
        await db_adapter.conn.execute("""
            INSERT INTO issues_new (
                ticket, issue_ticket, title, details, priority, 
                assignee_username, creator_id, message_id, topic_id, 
                status, created_at, claimed_at, resolved_at, escalated_at,
                claimed_by, resolved_by, rejected_by, escalation_sent, reminder_sent
            )
            SELECT 
                ticket, issue_ticket, title, details, priority,
                assignee_username, creator_id, message_id, topic_id,
                status, created_at, claimed_at, resolved_at, escalated_at,
                claimed_by, resolved_by, rejected_by, escalation_sent, reminder_sent
            FROM issues
        """)
        logger.info("Copied data from old issues table")
        
        # 3. Drop old table
        await db_adapter.conn.execute("DROP TABLE issues")
        logger.info("Dropped old issues table")
        
        # 4. Rename new table
        await db_adapter.conn.execute("ALTER TABLE issues_new RENAME TO issues")
        logger.info("Renamed new table to issues")
        
        # 5. Recreate the view if it was used (optional - may not be needed)
        # If the view is needed, it will be recreated by the application
        
        await db_adapter.conn.commit()
        logger.info("Migration 005 completed successfully")
        
        return True
    except Exception as e:
        logger.error(f"Migration 005 failed: {e}")
        await db_adapter.conn.rollback()
        raise


async def migrate_down(db_adapter):
    """Rollback migration 005."""
    try:
        logger.warning("Rollback not supported for this migration")
        return True
    except Exception as e:
        logger.error(f"Migration 005 rollback failed: {e}")
        raise
