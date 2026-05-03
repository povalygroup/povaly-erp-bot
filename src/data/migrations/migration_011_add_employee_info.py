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
        
        # Get existing columns
        cursor = await db.conn.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in await cursor.fetchall()}
        logger.info(f"Existing columns in users table: {existing_columns}")
        
        # Helper function to add column if it doesn't exist
        async def add_column_if_not_exists(column_name, column_type, default=None):
            if column_name not in existing_columns:
                default_clause = f" DEFAULT {default}" if default is not None else ""
                await db.conn.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}{default_clause}")
                logger.info(f"Added column: {column_name}")
            else:
                logger.info(f"Column already exists, skipping: {column_name}")
        
        # Add employee information columns to users table
        await add_column_if_not_exists("first_name", "TEXT")
        await add_column_if_not_exists("last_name", "TEXT")
        await add_column_if_not_exists("full_name", "TEXT")
        await add_column_if_not_exists("email", "TEXT")
        await add_column_if_not_exists("phone", "TEXT")
        await add_column_if_not_exists("department", "TEXT")
        await add_column_if_not_exists("position", "TEXT")
        await add_column_if_not_exists("join_date", "TEXT")
        await add_column_if_not_exists("emergency_contact", "TEXT")
        await add_column_if_not_exists("blood_group", "TEXT")
        await add_column_if_not_exists("address", "TEXT")
        await add_column_if_not_exists("skills", "TEXT")
        await add_column_if_not_exists("notes", "TEXT")
        
        # Add birthday information columns
        await add_column_if_not_exists("birth_date", "TEXT")
        await add_column_if_not_exists("birth_day", "INTEGER")
        await add_column_if_not_exists("birth_month", "INTEGER")
        await add_column_if_not_exists("birth_year", "INTEGER")
        await add_column_if_not_exists("birthday_wishes_sent", "TEXT")
        await add_column_if_not_exists("custom_birthday_message", "TEXT")
        await add_column_if_not_exists("birthday_reminder_sent", "TEXT")
        
        # Add metadata columns
        await add_column_if_not_exists("info_set_by", "TEXT")
        await add_column_if_not_exists("info_updated_at", "TEXT")
        await add_column_if_not_exists("info_complete", "INTEGER", 0)
        
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
