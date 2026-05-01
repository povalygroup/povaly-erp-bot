"""
Migration 002: Add timestamp column to task_reactions table
NOTE: This migration has been integrated into the base schema.
The timestamp column is now part of the base task_reactions table definition.
This file is kept for historical reference only.
"""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db_adapter):
    """Apply migration - DEPRECATED: timestamp column now in base schema."""
    logger.info("Migration 002: Already integrated into base schema, skipping...")
    return True


async def migrate_down(db_adapter):
    """Rollback migration - DEPRECATED."""
    logger.info("Migration 002: Rollback not needed (integrated into base schema)")
    return True
