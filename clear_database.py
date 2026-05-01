"""Clear all data from the database."""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Clear all data from database."""
    db_path = "./data/povaly_bot.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        logger.info(f"Found {len(tables)} tables")
        
        # Delete all data from each table
        for table in tables:
            table_name = table[0]
            if table_name != 'migrations':  # Keep migration records
                cursor.execute(f"DELETE FROM {table_name}")
                logger.info(f"Cleared table: {table_name}")
        
        conn.commit()
        logger.info("✅ All data cleared successfully!")
        logger.info("Migration records kept - database structure intact")
        
    except Exception as e:
        logger.error(f"❌ Failed to clear database: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
