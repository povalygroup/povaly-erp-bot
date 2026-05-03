"""Migration 009: Add meeting tables for meeting invitations, attendees, notes, and reactions."""

import logging

logger = logging.getLogger(__name__)


async def migrate_up(db_adapter):
    """Apply migration - create meeting-related tables."""
    try:
        # Create meetings table
        await db_adapter.conn.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                meeting_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                date TIMESTAMP NOT NULL,
                duration_minutes INTEGER NOT NULL,
                location TEXT NOT NULL,
                organizer_id INTEGER NOT NULL,
                agenda TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                message_id INTEGER NOT NULL UNIQUE,
                topic_id INTEGER NOT NULL,
                preparation TEXT,
                notes_message_id INTEGER,
                cancelled_reason TEXT,
                rescheduled_to TEXT,
                reminded_24h_at TIMESTAMP,
                reminded_1h_at TIMESTAMP,
                reminded_15m_at TIMESTAMP,
                completed_at TIMESTAMP,
                cancelled_at TIMESTAMP
            )
        """)
        
        # Create meeting_attendees table
        await db_adapter.conn.execute("""
            CREATE TABLE IF NOT EXISTS meeting_attendees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                invited_at TIMESTAMP NOT NULL,
                responded_at TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE,
                UNIQUE(meeting_id, user_id)
            )
        """)
        
        # Create meeting_notes table
        await db_adapter.conn.execute("""
            CREATE TABLE IF NOT EXISTS meeting_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id TEXT NOT NULL,
                posted_by INTEGER NOT NULL,
                posted_at TIMESTAMP NOT NULL,
                message_id INTEGER NOT NULL UNIQUE,
                attendees_present TEXT NOT NULL,
                decisions TEXT NOT NULL,
                action_items TEXT NOT NULL,
                next_meeting_date TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE
            )
        """)
        
        # Create meeting_reactions table (for RSVP tracking)
        await db_adapter.conn.execute("""
            CREATE TABLE IF NOT EXISTS meeting_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reaction TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE,
                UNIQUE(meeting_id, user_id, reaction)
            )
        """)
        
        # Create indexes for meetings table
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meetings_message_id 
            ON meetings(message_id)
        """)
        
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meetings_organizer_id 
            ON meetings(organizer_id)
        """)
        
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meetings_date 
            ON meetings(date)
        """)
        
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meetings_status 
            ON meetings(status)
        """)
        
        # Create indexes for meeting_attendees table
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meeting_attendees_meeting_id 
            ON meeting_attendees(meeting_id)
        """)
        
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meeting_attendees_user_id 
            ON meeting_attendees(user_id)
        """)
        
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meeting_attendees_status 
            ON meeting_attendees(status)
        """)
        
        # Create indexes for meeting_notes table
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meeting_notes_meeting_id 
            ON meeting_notes(meeting_id)
        """)
        
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meeting_notes_message_id 
            ON meeting_notes(message_id)
        """)
        
        # Create indexes for meeting_reactions table
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meeting_reactions_meeting_id 
            ON meeting_reactions(meeting_id)
        """)
        
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meeting_reactions_user_id 
            ON meeting_reactions(user_id)
        """)
        
        await db_adapter.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meeting_reactions_message_id 
            ON meeting_reactions(message_id)
        """)
        
        logger.info("✅ Migration 009: Meeting tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 009 failed: {e}")
        return False


async def migrate_down(db_adapter):
    """Rollback migration - drop meeting-related tables."""
    try:
        await db_adapter.conn.execute("DROP TABLE IF EXISTS meeting_reactions")
        await db_adapter.conn.execute("DROP TABLE IF EXISTS meeting_notes")
        await db_adapter.conn.execute("DROP TABLE IF EXISTS meeting_attendees")
        await db_adapter.conn.execute("DROP TABLE IF EXISTS meetings")
        
        logger.info("✅ Migration 009 rollback: Meeting tables dropped")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 009 rollback failed: {e}")
        return False
