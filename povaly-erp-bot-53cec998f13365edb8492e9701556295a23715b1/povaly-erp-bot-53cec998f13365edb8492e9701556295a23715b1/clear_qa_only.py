"""Clear only QA data from the database."""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Clear only QA data from database."""
    db_path = "./data/povaly_bot.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Delete all data from QA tables and related tables
        cursor.execute("DELETE FROM qa_reactions")
        reactions_deleted = cursor.rowcount
        logger.info(f"Cleared {reactions_deleted} QA reactions")
        
        cursor.execute("DELETE FROM qa_reviewers")
        reviewers_deleted = cursor.rowcount
        logger.info(f"Cleared {reviewers_deleted} QA reviewers")
        
        cursor.execute("DELETE FROM qa_submissions")
        submissions_deleted = cursor.rowcount
        logger.info(f"Cleared {submissions_deleted} QA submissions")
        
        conn.commit()
        logger.info(f"✅ Successfully cleared all QA-related data")
        logger.info("All other data (tasks, users, issues, etc.) remains intact")
        
    except Exception as e:
        logger.error(f"❌ Failed to clear QA data: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
