"""Task repository for data access."""

from typing import Optional, List
from datetime import datetime

from src.data.models import Task, TaskState, TaskReaction, RejectFeedback, Archive


class TaskRepository:
    """Repository for task-related data operations."""
    
    def __init__(self, db):
        """Initialize with database adapter."""
        self.db = db
    
    async def create_task(self, task: Task) -> None:
        """Create a new task."""
        await self.db.insert_task(task)
    
    async def get_task(self, ticket: str) -> Optional[Task]:
        """Get task by ticket ID."""
        return await self.db.get_task_by_ticket(ticket)
    
    async def get_task_by_message_id(self, message_id: int) -> Optional[Task]:
        """Get task by message ID."""
        return await self.db.get_task_by_message_id(message_id)
    
    async def update_task_state(self, ticket: str, state: TaskState, timestamp: Optional[datetime] = None) -> None:
        """Update task state."""
        await self.db.update_task_state(ticket, state, timestamp)
    
    async def get_tasks_by_assignee(self, assignee_id: int, state: Optional[TaskState] = None) -> List[Task]:
        """Get tasks assigned to a user."""
        return await self.db.get_tasks_by_assignee(assignee_id, state)
    
    async def get_tasks_by_state(self, state: TaskState) -> List[Task]:
        """Get all tasks in a specific state."""
        return await self.db.get_tasks_by_state(state)
    
    async def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return await self.db.get_all_tasks()
    
    async def get_tasks_created_after(self, timestamp: datetime) -> List[Task]:
        """Get tasks created after a specific time."""
        return await self.db.get_tasks_created_after(timestamp)
    
    async def add_reaction(self, ticket: str, emoji: str, user_id: int, message_id: int, topic_id: int) -> None:
        """Add a reaction to a task (simplified version for reaction handler)."""
        reaction = TaskReaction(
            id=None,
            message_id=message_id,
            ticket=ticket,
            user_id=user_id,
            reaction=emoji,
            timestamp=datetime.now(),
            topic_id=topic_id
        )
        await self.db.insert_reaction(reaction)
    
    async def remove_fire_exemption(self, ticket: str) -> None:
        """Remove fire exemption from a task."""
        await self.db.update_fire_exemption(ticket, None, None)
    
    async def get_first_reaction(self, ticket: str, reaction_type: str) -> Optional[TaskReaction]:
        """Get the first reaction of a specific type for a task."""
        return await self.db.get_first_reaction(ticket, reaction_type)
    
    async def remove_reaction(self, ticket: str, user_id: int, reaction_type: str) -> None:
        """Remove a reaction from the database."""
        await self.db.remove_reaction(ticket, user_id, reaction_type)
    
    async def get_reactions_by_message(self, message_id: int) -> List[TaskReaction]:
        """Get all reactions for a message."""
        return await self.db.get_reactions_by_message(message_id)
    
    async def get_task_reactions(self, ticket: str) -> List[dict]:
        """Get all reactions for a task."""
        reactions = await self.db.get_reactions_by_ticket(ticket)
        return [
            {
                'user_id': r.user_id,
                'emoji': r.reaction,
                'timestamp': r.timestamp
            }
            for r in reactions
        ]
    
    async def add_reject_feedback(self, feedback: RejectFeedback) -> None:
        """Add reject feedback."""
        await self.db.insert_reject_feedback(feedback)
    
    async def get_reject_feedback(self, ticket: str) -> Optional[RejectFeedback]:
        """Get reject feedback for a task."""
        return await self.db.get_reject_feedback_by_ticket(ticket)
    
    async def archive_task(self, archive: Archive) -> None:
        """Archive a completed task."""
        await self.db.insert_archive(archive)
    
    async def get_archive(self, ticket: str) -> Optional[Archive]:
        """Get archived task."""
        return await self.db.get_archive_by_ticket(ticket)
    
    async def update_fire_exemption(self, ticket: str, user_id: int, timestamp: datetime) -> None:
        """Update fire emoji exemption for a task."""
        await self.db.update_fire_exemption(ticket, user_id, timestamp)
    
    async def get_pending_tasks_without_fire(self, before_date: datetime) -> List[Task]:
        """Get pending tasks without fire exemption created before a date."""
        return await self.db.get_pending_tasks_without_fire(before_date)
    
    # Task dependency operations
    
    async def add_dependency(self, ticket: str, blocked_by_ticket: str, created_by: int) -> bool:
        """Add a dependency - ticket is blocked by blocked_by_ticket."""
        return await self.db.add_task_dependency(ticket, blocked_by_ticket, created_by)
    
    async def remove_dependency(self, ticket: str, blocked_by_ticket: str) -> bool:
        """Remove a dependency."""
        return await self.db.remove_task_dependency(ticket, blocked_by_ticket)
    
    async def get_blocking_tasks(self, ticket: str) -> List[str]:
        """Get all tasks that are blocking this ticket."""
        return await self.db.get_blocking_tasks(ticket)
    
    async def get_blocked_tasks(self, ticket: str) -> List[str]:
        """Get all tasks that are blocked by this ticket."""
        return await self.db.get_blocked_tasks(ticket)
    
    async def has_blocking_tasks(self, ticket: str) -> bool:
        """Check if ticket has any blocking tasks."""
        return await self.db.has_blocking_tasks(ticket)
