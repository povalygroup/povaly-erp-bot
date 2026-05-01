"""Check for duplicate issues in the database."""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Check for duplicate issues."""
    db_path = "./data/povaly_bot.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Find duplicate tickets
        cursor.execute("""
            SELECT ticket, COUNT(*) as count
            FROM issues
            GROUP BY ticket
            HAVING count > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            logger.info("✅ No duplicate issues found")
            return
        
        logger.warning(f"⚠️ Found {len(duplicates)} tickets with duplicates:")
        
        for ticket, count in duplicates:
            logger.warning(f"  - {ticket}: {count} records")
            
            # Show details of each duplicate
            cursor.execute("""
                SELECT issue_ticket, ticket, title, status, escalation_sent, created_at
                FROM issues
                WHERE ticket = ?
                ORDER BY created_at
            """, (ticket,))
            
            records = cursor.fetchall()
            for i, record in enumerate(records, 1):
                issue_ticket, ticket, title, status, escalation_sent, created_at = record
                logger.info(f"    {i}. issue_ticket={issue_ticket}, status={status}, escalation_sent={escalation_sent}, created_at={created_at}")
        
        # Ask if user wants to clean up
        print("\n" + "="*60)
        print("Would you like to remove duplicate issues? (y/n)")
        print("This will keep only the OLDEST record for each ticket.")
        print("="*60)
        
        response = input("> ").strip().lower()
        
        if response == 'y':
            for ticket, count in duplicates:
                # Keep only the oldest record (first created)
                cursor.execute("""
                    DELETE FROM issues
                    WHERE ticket = ?
                    AND issue_ticket NOT IN (
                        SELECT issue_ticket
                        FROM issues
                        WHERE ticket = ?
                        ORDER BY created_at ASC
                        LIMIT 1
                    )
                """, (ticket, ticket))
                
                deleted = cursor.rowcount
                logger.info(f"✅ Removed {deleted} duplicate(s) for ticket {ticket}")
            
            conn.commit()
            logger.info("✅ Cleanup complete")
        else:
            logger.info("Cleanup cancelled")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
