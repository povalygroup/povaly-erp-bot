"""Migration 004: Add issue_ticket column to issues table."""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db_adapter):
    """Add issue_ticket column to issues table."""
    try:
        # Add issue_ticket column
        await db_adapter.execute_query(
            "ALTER TABLE issues ADD COLUMN issue_ticket TEXT"
        )
        logger.info("Added issue_ticket column to issues table")
        
        # Update existing issues to have issue_ticket = ticket-I1
        # This assumes existing issues are the first issue for their task
        await db_adapter.execute_query(
            "UPDATE issues SET issue_ticket = ticket || '-I1' WHERE issue_ticket IS NULL"
        )
        logger.info("Updated existing issues with issue_ticket values")
        
        return True
    except Exception as e:
        logger.error(f"Migration 004 failed: {e}")
        raise


async def migrate_down(db_adapter):
    """Remove issue_ticket column from issues table."""
    try:
        # SQLite doesn't support DROP COLUMN directly in older versions
        # This is a placeholder for potential rollback
        logger.warning("Downgrade not fully supported for this migration")
        return True
    except Exception as e:
        logger.error(f"Migration 004 downgrade failed: {e}")
        raise
