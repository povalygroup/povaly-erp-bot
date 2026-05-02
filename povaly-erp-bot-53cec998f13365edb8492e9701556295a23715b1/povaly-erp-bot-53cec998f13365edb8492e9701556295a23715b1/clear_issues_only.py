"""Clear only issues data from the database."""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Clear only issues data from database."""
    db_path = "./data/povaly_bot.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Delete all data from issues table and related tables
        cursor.execute("DELETE FROM issue_reactions")
        reactions_deleted = cursor.rowcount
        logger.info(f"Cleared {reactions_deleted} issue reactions")
        
        cursor.execute("DELETE FROM issue_handlers")
        handlers_deleted = cursor.rowcount
        logger.info(f"Cleared {handlers_deleted} issue handlers")
        
        cursor.execute("DELETE FROM issues")
        issues_deleted = cursor.rowcount
        logger.info(f"Cleared {issues_deleted} issues")
        
        conn.commit()
        logger.info(f"✅ Successfully cleared all issue-related data")
        logger.info("All other data (tasks, users, etc.) remains intact")
        
    except Exception as e:
        logger.error(f"❌ Failed to clear issues: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
