#!/usr/bin/env python3
"""
Database migration script to add missing last_overdue_alert_date column to tasks table.
This ensures VPS database matches local database schema.
"""

import sqlite3
import sys

def migrate_database(db_path):
    """Add last_overdue_alert_date column if it doesn't exist."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'last_overdue_alert_date' in column_names:
            print("✅ Column 'last_overdue_alert_date' already exists")
            conn.close()
            return True
        
        # Add the missing column
        print("Adding 'last_overdue_alert_date' column to tasks table...")
        cursor.execute("""
            ALTER TABLE tasks 
            ADD COLUMN last_overdue_alert_date TEXT
        """)
        conn.commit()
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        print(f"\n✅ Migration successful! Tasks table now has {len(columns)} columns:")
        for col in columns:
            cid, name, type_, notnull, dflt_value, pk = col
            print(f"   {cid}: {name} ({type_})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_db.py <database_path>")
        print("Example: python migrate_db.py ~/povaly-bot/data/povaly_erp_bot.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
