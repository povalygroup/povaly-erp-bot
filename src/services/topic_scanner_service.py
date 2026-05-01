"""Topic scanner service to read actual tasks from Task Allocation topic."""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

from src.core.parser.message_parser import MessageParser
from src.data.models.task import TaskState

logger = logging.getLogger(__name__)


@dataclass
class TopicTask:
    """Represents a task found in the topic."""
    ticket: str
    assignee_username: str
    assignee_id: Optional[int]  # Will be resolved from username
    brand: str
    message_id: int
    message_date: datetime
    message_text: str
    topic_id: int


class TopicScannerService:
    """Service to scan Task Allocation topic and find actual tasks."""
    
    def __init__(self, config, task_service):
        """Initialize the topic scanner."""
        self.config = config
        self.task_service = task_service
        self.parser = MessageParser()
        
        # Cache of scanned tasks
        self.topic_tasks: Dict[int, List[TopicTask]] = {}  # user_id -> list of tasks
        self.last_scan_time: Optional[datetime] = None
        
    async def scan_task_allocation_topic(self, application) -> Dict[int, List[TopicTask]]:
        """
        Scan the Task Allocation topic to find all actual tasks.
        Returns dict of user_id -> list of TopicTask objects.
        """
        try:
            logger.info("🔍 Scanning Task Allocation topic for actual tasks...")
            
            # Clear previous scan results
            self.topic_tasks.clear()
            
            # We'll use a different approach since we can't directly iterate chat history
            # Instead, we'll scan recent messages using get_chat API
            
            chat_id = self.config.TELEGRAM_GROUP_ID
            topic_id = self.config.TOPIC_TASK_ALLOCATION
            
            # Try to get recent messages from the topic
            # This is a workaround since we can't use iter_chat_history
            found_tasks = await self._scan_topic_messages(application, chat_id, topic_id)
            
            # Group tasks by user
            for task in found_tasks:
                if task.assignee_id:
                    if task.assignee_id not in self.topic_tasks:
                        self.topic_tasks[task.assignee_id] = []
                    self.topic_tasks[task.assignee_id].append(task)
            
            # Sort tasks by date (most recent first) for each user
            for user_id in self.topic_tasks:
                self.topic_tasks[user_id].sort(key=lambda t: t.message_date, reverse=True)
            
            total_tasks = sum(len(tasks) for tasks in self.topic_tasks.values())
            total_users = len(self.topic_tasks)
            
            logger.info(f"✅ Topic scan completed: found {total_tasks} tasks for {total_users} users")
            
            self.last_scan_time = datetime.now()
            return self.topic_tasks.copy()
            
        except Exception as e:
            logger.error(f"❌ Error scanning Task Allocation topic: {e}")
            return {}
    
    async def _scan_topic_messages(self, application, chat_id: int, topic_id: int) -> List[TopicTask]:
        """
        Scan messages in the topic to find tasks.
        This is a workaround approach since we can't use iter_chat_history.
        """
        found_tasks = []
        
        try:
            # Since we can't directly read chat history, we'll use a different approach
            # We'll try to get the topic info and recent messages
            
            # For now, we'll implement a placeholder that shows the concept
            # In a real implementation, you might need to:
            # 1. Use a user bot (not bot API) to read messages
            # 2. Store message IDs when tasks are created and scan those
            # 3. Use webhooks to track all messages
            
            logger.warning("⚠️ Direct topic scanning not available with Bot API limitations")
            logger.info("💡 Using database-assisted scanning approach instead")
            
            # Alternative approach: Use database to find recent tasks and validate them
            found_tasks = await self._database_assisted_scan(application, chat_id, topic_id)
            
        except Exception as e:
            logger.error(f"Error scanning topic messages: {e}")
        
        return found_tasks
    
    async def _database_assisted_scan(self, application, chat_id: int, topic_id: int) -> List[TopicTask]:
        """
        Database-assisted scanning: Use database tasks as source of truth.
        Don't delete tasks just because we can't validate them via Bot API.
        """
        found_tasks = []
        
        try:
            # Get all active tasks from database
            all_tasks = await self.task_service.task_repo.db.fetch_all(
                "SELECT * FROM tasks WHERE state IN (?, ?, ?, ?) AND topic_id = ?",
                (TaskState.ASSIGNED.value, TaskState.STARTED.value, 
                 TaskState.QA_SUBMITTED.value, TaskState.REJECTED.value, topic_id)
            )
            
            logger.info(f"🔍 Found {len(all_tasks)} tasks in database for topic {topic_id}")
            
            # Use database as source of truth - don't try to validate via Bot API
            # because get_message() is not available in Bot API
            for task_data in all_tasks:
                try:
                    # Create TopicTask from database data
                    topic_task = TopicTask(
                        ticket=task_data['ticket'],
                        assignee_username="",  # We don't store this in DB
                        assignee_id=task_data['assignee_id'],
                        brand=task_data['brand'],
                        message_id=task_data['message_id'],
                        message_date=datetime.fromisoformat(task_data['created_at']),
                        message_text="",  # We don't store this in DB
                        topic_id=topic_id
                    )
                    found_tasks.append(topic_task)
                    logger.debug(f"✅ Loaded task {task_data['ticket']} from database")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not load task {task_data['ticket']}: {e}")
                    continue
            
            logger.info(f"✅ Loaded {len(found_tasks)} tasks from database")
            
        except Exception as e:
            logger.error(f"Error in database-assisted scan: {e}")
        
        return found_tasks
    
    async def get_user_tasks_from_topic(self, user_id: int) -> List[TopicTask]:
        """Get all tasks for a specific user from the last topic scan."""
        return self.topic_tasks.get(user_id, [])
    
    async def sync_database_with_topic_reality(self, application) -> Dict[str, int]:
        """
        Sync database with actual topic reality.
        Returns statistics about what was synced.
        """
        try:
            logger.info("🔄 Starting database sync with topic reality...")
            
            # Scan the topic to get actual tasks
            topic_tasks = await self.scan_task_allocation_topic(application)
            
            stats = {
                "users_scanned": 0,
                "tasks_found_in_topic": 0,
                "tasks_removed_from_db": 0,
                "tasks_added_to_db": 0,
                "users_synced": 0
            }
            
            # Get all users who have tasks in either topic or database
            all_user_ids = set()
            
            # Users from topic scan
            all_user_ids.update(topic_tasks.keys())
            
            # Users from database
            db_users = await self.task_service.task_repo.db.fetch_all(
                "SELECT DISTINCT assignee_id FROM tasks WHERE state IN (?, ?, ?, ?)",
                (TaskState.ASSIGNED.value, TaskState.STARTED.value, 
                 TaskState.QA_SUBMITTED.value, TaskState.REJECTED.value)
            )
            all_user_ids.update(user['assignee_id'] for user in db_users)
            
            stats["users_scanned"] = len(all_user_ids)
            
            # Sync each user
            for user_id in all_user_ids:
                user_stats = await self._sync_user_with_topic(user_id, topic_tasks.get(user_id, []))
                
                stats["tasks_found_in_topic"] += user_stats["topic_tasks"]
                stats["tasks_removed_from_db"] += user_stats["removed"]
                stats["tasks_added_to_db"] += user_stats["added"]
                
                if user_stats["removed"] > 0 or user_stats["added"] > 0:
                    stats["users_synced"] += 1
            
            logger.info(f"✅ Database sync completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error syncing database with topic reality: {e}")
            return {"error": str(e)}
    
    async def _sync_user_with_topic(self, user_id: int, topic_tasks: List[TopicTask]) -> Dict[str, int]:
        """
        Sync a specific user's database tasks with their topic tasks.
        Detects deleted tasks (in DB but not in topic) and marks them as ARCHIVED.
        """
        try:
            # Get user's tasks from database
            db_tasks = await self.task_service.task_repo.get_tasks_by_assignee(user_id)
            active_states = [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.REJECTED]
            active_db_tasks = [t for t in db_tasks if t.state in active_states]
            
            # Create sets of ticket IDs for comparison
            topic_tickets = {task.ticket for task in topic_tasks}
            db_tickets = {task.ticket for task in active_db_tasks}
            
            # Find deleted tasks (in DB but not in topic)
            deleted_tickets = db_tickets - topic_tickets
            removed_count = 0
            
            # Archive deleted tasks
            for ticket in deleted_tickets:
                try:
                    # Find the task and mark it as ARCHIVED
                    task = next((t for t in active_db_tasks if t.ticket == ticket), None)
                    if task:
                        await self.task_service.task_repo.update_task_state(ticket, TaskState.ARCHIVED)
                        logger.info(f"📦 Archived deleted task {ticket} for user {user_id}")
                        removed_count += 1
                except Exception as e:
                    logger.error(f"Error archiving task {ticket}: {e}")
            
            return {
                "topic_tasks": len(topic_tasks),
                "db_tasks": len(active_db_tasks),
                "removed": removed_count,  # Tasks marked as archived
                "added": 0     # We don't add tasks during sync
            }
            
        except Exception as e:
            logger.error(f"Error syncing user {user_id}: {e}")
            return {"topic_tasks": 0, "db_tasks": 0, "removed": 0, "added": 0}
    
    def get_scan_stats(self) -> Dict[str, any]:
        """Get statistics about the last topic scan."""
        if not self.last_scan_time:
            return {"status": "never_scanned"}
        
        total_tasks = sum(len(tasks) for tasks in self.topic_tasks.values())
        total_users = len(self.topic_tasks)
        
        return {
            "status": "scanned",
            "last_scan": self.last_scan_time,
            "total_users": total_users,
            "total_tasks": total_tasks,
            "users": {user_id: len(tasks) for user_id, tasks in self.topic_tasks.items()}
        }
    
    async def scan_recent_tasks_for_reactions(self, application, limit: int = 100):
        """
        Scan recent tasks from database to ensure they're ready for reaction handling.
        This is called on bot startup to register existing tasks.
        
        Args:
            application: Telegram application instance
            limit: Maximum number of recent tasks to scan
        """
        try:
            logger.info(f"🔍 Scanning last {limit} tasks for reaction handling...")
            
            # Get recent tasks from database (all active states)
            all_tasks = await self.task_service.task_repo.get_all_tasks()
            
            # Filter to active tasks only (not archived)
            active_tasks = [
                t for t in all_tasks 
                if t.state in [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.REJECTED, TaskState.APPROVED]
            ]
            
            # Sort by created_at descending and take last N
            active_tasks.sort(key=lambda t: t.created_at, reverse=True)
            recent_tasks = active_tasks[:limit]
            
            logger.info(f"✅ Found {len(recent_tasks)} recent active tasks in database")
            logger.info(f"   Tasks are ready for reaction handling (message_id stored in DB)")
            
            # Log some examples
            for i, task in enumerate(recent_tasks[:5]):
                logger.info(f"   {i+1}. {task.ticket} - message_id: {task.message_id}, state: {task.state.value}")
            
            if len(recent_tasks) > 5:
                logger.info(f"   ... and {len(recent_tasks) - 5} more tasks")
            
            return len(recent_tasks)
            
        except Exception as e:
            logger.error(f"❌ Error scanning recent tasks: {e}", exc_info=True)
            return 0