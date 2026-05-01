"""Task Assignee repository for managing multiple assignees per task."""

from typing import List, Optional
from datetime import datetime

from src.data.models.task import Task, TaskState


class TaskAssigneeRepository:
    """Repository for task assignee operations."""
    
    def __init__(self, db):
        """Initialize with database adapter."""
        self.db = db
    
    async def add_assignee(self, ticket: str, assignee_id: int, is_primary: bool = False):
        """Add an assignee to a task."""
        await self.db.conn.execute("""
            INSERT INTO task_assignees (ticket, assignee_id, status, assigned_at, is_primary)
            VALUES (?, ?, ?, ?, ?)
        """, (ticket, assignee_id, 'ASSIGNED', datetime.now().isoformat(), 1 if is_primary else 0))
        await self.db.conn.commit()
    
    async def get_assignees(self, ticket: str) -> List[dict]:
        """Get all assignees for a task."""
        async with self.db.conn.execute("""
            SELECT * FROM task_assignees WHERE ticket = ? ORDER BY assigned_at ASC
        """, (ticket,)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    async def get_assignee(self, ticket: str, assignee_id: int) -> Optional[dict]:
        """Get specific assignee for a task."""
        async with self.db.conn.execute("""
            SELECT * FROM task_assignees WHERE ticket = ? AND assignee_id = ?
        """, (ticket, assignee_id)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_assignee_status(self, ticket: str, assignee_id: int, status: str):
        """Update assignee status."""
        await self.db.conn.execute("""
            UPDATE task_assignees SET status = ? WHERE ticket = ? AND assignee_id = ?
        """, (status, ticket, assignee_id))
        await self.db.conn.commit()
    
    async def acknowledge_task(self, ticket: str, assignee_id: int):
        """Mark task as acknowledged by assignee."""
        await self.db.conn.execute("""
            UPDATE task_assignees 
            SET status = 'ACKNOWLEDGED', acknowledged_at = ?
            WHERE ticket = ? AND assignee_id = ?
        """, (datetime.now().isoformat(), ticket, assignee_id))
        await self.db.conn.commit()
    
    async def start_task(self, ticket: str, assignee_id: int):
        """Mark task as started by assignee."""
        await self.db.conn.execute("""
            UPDATE task_assignees 
            SET status = 'IN_PROGRESS', started_at = ?
            WHERE ticket = ? AND assignee_id = ?
        """, (datetime.now().isoformat(), ticket, assignee_id))
        await self.db.conn.commit()
    
    async def submit_task(self, ticket: str, assignee_id: int):
        """Mark task as submitted by assignee."""
        await self.db.conn.execute("""
            UPDATE task_assignees 
            SET status = 'SUBMITTED', submitted_at = ?
            WHERE ticket = ? AND assignee_id = ?
        """, (datetime.now().isoformat(), ticket, assignee_id))
        await self.db.conn.commit()
    
    async def complete_task(self, ticket: str, assignee_id: int):
        """Mark task as completed by assignee."""
        await self.db.conn.execute("""
            UPDATE task_assignees 
            SET status = 'COMPLETED', completed_at = ?
            WHERE ticket = ? AND assignee_id = ?
        """, (datetime.now().isoformat(), ticket, assignee_id))
        await self.db.conn.commit()
    
    async def remove_assignee(self, ticket: str, assignee_id: int):
        """Remove an assignee from a task."""
        await self.db.conn.execute("""
            DELETE FROM task_assignees WHERE ticket = ? AND assignee_id = ?
        """, (ticket, assignee_id))
        await self.db.conn.commit()
    
    async def get_tasks_by_assignee(self, assignee_id: int, status: Optional[str] = None) -> List[dict]:
        """Get all tasks assigned to a user."""
        if status:
            async with self.db.conn.execute("""
                SELECT ta.*, t.brand, t.state as task_state
                FROM task_assignees ta
                JOIN tasks t ON ta.ticket = t.ticket
                WHERE ta.assignee_id = ? AND ta.status = ?
                ORDER BY ta.assigned_at DESC
            """, (assignee_id, status)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]
        else:
            async with self.db.conn.execute("""
                SELECT ta.*, t.brand, t.state as task_state
                FROM task_assignees ta
                JOIN tasks t ON ta.ticket = t.ticket
                WHERE ta.assignee_id = ?
                ORDER BY ta.assigned_at DESC
            """, (assignee_id,)) as cursor:
                return [dict(row) for row in await cursor.fetchall()]
