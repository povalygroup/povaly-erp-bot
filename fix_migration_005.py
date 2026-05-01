"""Fix migration 005 - clean up and retry."""

import asyncio
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Fix migration 005."""
    db_path = "./data/povaly_bot.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Drop issues_new if it exists (from failed migration)
        cursor.execute("DROP TABLE IF EXISTS issues_new")
        logger.info("Dropped issues_new table if it existed")
        
        # 2. Remove migration record so it can run again
        cursor.execute("DELETE FROM migrations WHERE name = 'migration_005_fix_issue_constraints'")
        logger.info("Removed migration_005 record")
        
        conn.commit()
        logger.info("✅ Cleanup completed. Now restart the bot to run migration 005 again.")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())
