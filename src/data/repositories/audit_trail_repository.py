"""Audit Trail repository for tracking all changes."""

from typing import List, Optional
from datetime import datetime


class AuditTrailRepository:
    """Repository for audit trail operations."""
    
    def __init__(self, db):
        """Initialize with database adapter."""
        self.db = db
    
    async def log_action(self, ticket: str, action: str, changed_by: int, 
                        old_value: Optional[str] = None, new_value: Optional[str] = None,
                        context: Optional[str] = None):
        """Log an action to the audit trail."""
        await self.db.conn.execute("""
            INSERT INTO ticket_audit_trail 
            (ticket, action, old_value, new_value, changed_by, changed_at, context)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ticket, action, old_value, new_value, changed_by, datetime.now().isoformat(), context))
        await self.db.conn.commit()
    
    async def get_ticket_history(self, ticket: str) -> List[dict]:
        """Get complete history for a ticket."""
        async with self.db.conn.execute("""
            SELECT * FROM ticket_audit_trail 
            WHERE ticket = ?
            ORDER BY changed_at ASC
        """, (ticket,)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    async def get_ticket_timeline(self, ticket: str) -> List[dict]:
        """Get ticket timeline with all events."""
        # Get task events
        task_events = []
        async with self.db.conn.execute("""
            SELECT 
                'TASK_CREATED' as event,
                created_at as timestamp,
                creator_id as user_id,
                NULL as context
            FROM tasks
            WHERE ticket = ?
        """, (ticket,)) as cursor:
            task_events.extend([dict(row) for row in await cursor.fetchall()])
        
        # Get assignee acknowledgments
        async with self.db.conn.execute("""
            SELECT 
                'TASK_ACKNOWLEDGED' as event,
                acknowledged_at as timestamp,
                assignee_id as user_id,
                CAST(assignee_id AS TEXT) as context
            FROM task_assignees
            WHERE ticket = ? AND acknowledged_at IS NOT NULL
        """, (ticket,)) as cursor:
            task_events.extend([dict(row) for row in await cursor.fetchall()])
        
        # Get issue events
        async with self.db.conn.execute("""
            SELECT 
                'ISSUE_CREATED' as event,
                created_at as timestamp,
                creator_id as user_id,
                CAST(id AS TEXT) as context
            FROM issues
            WHERE ticket = ?
        """, (ticket,)) as cursor:
            task_events.extend([dict(row) for row in await cursor.fetchall()])
        
        # Get QA events
        async with self.db.conn.execute("""
            SELECT 
                'QA_SUBMITTED' as event,
                submitted_at as timestamp,
                submitter_id as user_id,
                CAST(id AS TEXT) as context
            FROM qa_submissions
            WHERE ticket = ?
        """, (ticket,)) as cursor:
            task_events.extend([dict(row) for row in await cursor.fetchall()])
        
        # Sort by timestamp
        task_events.sort(key=lambda x: x['timestamp'] or '')
        return task_events
    
    async def get_actions_by_user(self, user_id: int, limit: int = 100) -> List[dict]:
        """Get all actions performed by a user."""
        async with self.db.conn.execute("""
            SELECT * FROM ticket_audit_trail 
            WHERE changed_by = ?
            ORDER BY changed_at DESC
            LIMIT ?
        """, (user_id, limit)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    async def get_actions_by_type(self, action: str, limit: int = 100) -> List[dict]:
        """Get all actions of a specific type."""
        async with self.db.conn.execute("""
            SELECT * FROM ticket_audit_trail 
            WHERE action = ?
            ORDER BY changed_at DESC
            LIMIT ?
        """, (action, limit)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    async def get_recent_actions(self, limit: int = 50) -> List[dict]:
        """Get recent actions across all tickets."""
        async with self.db.conn.execute("""
            SELECT * FROM ticket_audit_trail 
            ORDER BY changed_at DESC
            LIMIT ?
        """, (limit,)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
