"""Reaction repository for tracking all reactions."""

from typing import List, Optional
from datetime import datetime


class ReactionRepository:
    """Repository for reaction tracking."""
    
    def __init__(self, db):
        """Initialize with database adapter."""
        self.db = db
    
    # Task Reactions
    async def add_task_reaction(self, ticket: str, message_id: int, reaction: str, 
                               user_id: int, context: Optional[str] = None):
        """Add a reaction to a task."""
        await self.db.conn.execute("""
            INSERT INTO task_reactions (ticket, message_id, reaction, user_id, context, reacted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ticket, message_id, reaction, user_id, context, datetime.now().isoformat()))
        await self.db.conn.commit()
    
    async def get_task_reactions(self, ticket: str) -> List[dict]:
        """Get all reactions for a task."""
        async with self.db.conn.execute("""
            SELECT * FROM task_reactions WHERE ticket = ? ORDER BY reacted_at ASC
        """, (ticket,)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    async def get_task_reaction_by_type(self, ticket: str, reaction: str) -> List[dict]:
        """Get specific reaction type for a task."""
        async with self.db.conn.execute("""
            SELECT * FROM task_reactions WHERE ticket = ? AND reaction = ? ORDER BY reacted_at ASC
        """, (ticket, reaction)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    # Issue Reactions
    async def add_issue_reaction(self, issue_id: int, message_id: int, reaction: str,
                                user_id: int, context: Optional[str] = None):
        """Add a reaction to an issue."""
        await self.db.conn.execute("""
            INSERT INTO issue_reactions (issue_id, message_id, reaction, user_id, context, reacted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (issue_id, message_id, reaction, user_id, context, datetime.now().isoformat()))
        await self.db.conn.commit()
    
    async def get_issue_reactions(self, issue_id: int) -> List[dict]:
        """Get all reactions for an issue."""
        async with self.db.conn.execute("""
            SELECT * FROM issue_reactions WHERE issue_id = ? ORDER BY reacted_at ASC
        """, (issue_id,)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    async def get_issue_reaction_by_type(self, issue_id: int, reaction: str) -> List[dict]:
        """Get specific reaction type for an issue."""
        async with self.db.conn.execute("""
            SELECT * FROM issue_reactions WHERE issue_id = ? AND reaction = ? ORDER BY reacted_at ASC
        """, (issue_id, reaction)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    # QA Reactions
    async def add_qa_reaction(self, qa_submission_id: int, message_id: int, reaction: str,
                             user_id: int, context: Optional[str] = None):
        """Add a reaction to a QA submission."""
        await self.db.conn.execute("""
            INSERT INTO qa_reactions (qa_submission_id, message_id, reaction, user_id, context, reacted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (qa_submission_id, message_id, reaction, user_id, context, datetime.now().isoformat()))
        await self.db.conn.commit()
    
    async def get_qa_reactions(self, qa_submission_id: int) -> List[dict]:
        """Get all reactions for a QA submission."""
        async with self.db.conn.execute("""
            SELECT * FROM qa_reactions WHERE qa_submission_id = ? ORDER BY reacted_at ASC
        """, (qa_submission_id,)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    async def get_qa_reaction_by_type(self, qa_submission_id: int, reaction: str) -> List[dict]:
        """Get specific reaction type for a QA submission."""
        async with self.db.conn.execute("""
            SELECT * FROM qa_reactions WHERE qa_submission_id = ? AND reaction = ? ORDER BY reacted_at ASC
        """, (qa_submission_id, reaction)) as cursor:
            return [dict(row) for row in await cursor.fetchall()]
    
    # Reaction removal
    async def remove_task_reaction(self, ticket: str, reaction: str, user_id: int):
        """Remove a reaction from a task."""
        await self.db.conn.execute("""
            UPDATE task_reactions 
            SET removed_at = ?
            WHERE ticket = ? AND reaction = ? AND user_id = ? AND removed_at IS NULL
        """, (datetime.now().isoformat(), ticket, reaction, user_id))
        await self.db.conn.commit()
    
    async def remove_issue_reaction(self, issue_id: int, reaction: str, user_id: int):
        """Remove a reaction from an issue."""
        await self.db.conn.execute("""
            UPDATE issue_reactions 
            SET removed_at = ?
            WHERE issue_id = ? AND reaction = ? AND user_id = ? AND removed_at IS NULL
        """, (datetime.now().isoformat(), issue_id, reaction, user_id))
        await self.db.conn.commit()
    
    async def remove_qa_reaction(self, qa_submission_id: int, reaction: str, user_id: int):
        """Remove a reaction from a QA submission."""
        await self.db.conn.execute("""
            UPDATE qa_reactions 
            SET removed_at = ?
            WHERE qa_submission_id = ? AND reaction = ? AND user_id = ? AND removed_at IS NULL
        """, (datetime.now().isoformat(), qa_submission_id, reaction, user_id))
        await self.db.conn.commit()
