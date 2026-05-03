"""
Migration 011: Add Employee Information and Birthday System

This migration adds comprehensive employee information fields and birthday tracking.
"""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db):
    """Add employee information and birthday fields to users table."""
    try:
        logger.info("Running migration 011: Add employee information and birthday system")
        
        # Add employee information columns to users table
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN full_name TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN email TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN phone TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN department TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN position TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN join_date TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN emergency_contact TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN blood_group TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN address TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN skills TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN notes TEXT
        """)
        
        # Add birthday information columns
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN birth_date TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN birth_day INTEGER
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN birth_month INTEGER
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN birth_year INTEGER
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN birthday_wishes_sent TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN custom_birthday_message TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN birthday_reminder_sent TEXT
        """)
        
        # Add metadata columns
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN info_set_by TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN info_updated_at TEXT
        """)
        
        await db.conn.execute("""
            ALTER TABLE users ADD COLUMN info_complete INTEGER DEFAULT 0
        """)
        
        # Create birthday_wishes table
        await db.conn.execute("""
            CREATE TABLE IF NOT EXISTS birthday_wishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                wish_date TEXT NOT NULL,
                wish_type TEXT NOT NULL,
                custom_message TEXT,
                sent_by_user_id INTEGER,
                dm_sent INTEGER DEFAULT 0,
                group_sent INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Create birthday_reminders table
        await db.conn.execute("""
            CREATE TABLE IF NOT EXISTS birthday_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reminder_date TEXT NOT NULL,
                birthday_date TEXT NOT NULL,
                user_dm_sent INTEGER DEFAULT 0,
                admin_dm_sent INTEGER DEFAULT 0,
                group_sent INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Create indexes for performance
        await db.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_birth_month_day 
            ON users(birth_month, birth_day)
        """)
        
        await db.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        """)
        
        await db.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_department 
            ON users(department)
        """)
        
        await db.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_birthday_wishes_user_date 
            ON birthday_wishes(user_id, wish_date)
        """)
        
        await db.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_birthday_reminders_user_date 
            ON birthday_reminders(user_id, reminder_date)
        """)
        
        await db.conn.commit()
        
        logger.info("✅ Migration 011 completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Migration 011 failed: {e}")
        raise


async def migrate_down(db):
    """Remove employee information and birthday fields (not recommended)."""
    try:
        logger.info("Running migration 011 downgrade")
        
        # Note: SQLite doesn't support DROP COLUMN directly
        # This is a placeholder for documentation purposes
        # In production, you would need to recreate the table without these columns
        
        await db.conn.execute("DROP TABLE IF EXISTS birthday_reminders")
        await db.conn.execute("DROP TABLE IF EXISTS birthday_wishes")
        
        await db.conn.commit()
        
        logger.info("✅ Migration 011 downgrade completed")
        logger.warning("⚠️ User table columns cannot be dropped in SQLite without recreating table")
        
    except Exception as e:
        logger.error(f"❌ Migration 011 downgrade failed: {e}")
        raise
