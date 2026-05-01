"""Database synchronization service for automatic cleanup."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, Optional

from src.data.models.task import TaskState

logger = logging.getLogger(__name__)


class DatabaseSyncService:
    """
    Service for automatic database synchronization with topic reality.
    
    IMPORTANT: Automatic sync is currently DISABLED due to aggressive deletion behavior.
    The service was deleting valid tasks because:
    1. topic_reality tracking was not comprehensive enough
    2. Tasks created before bot startup were not tracked
    3. Race conditions between task creation and tracking
    
    Current behavior:
    - Reality tracking is active (tracks task creation/deletion)
    - Automatic sync loop is disabled (does not delete tasks)
    - Manual sync commands still work for administrators
    
    TODO: Redesign sync logic to be more conservative:
    - Only delete tasks that are confirmed deleted from Telegram
    - Add grace period before deletion
    - Require multiple confirmations before deletion
    - Better handling of bot restarts
    """
    
    def __init__(self, task_service, config, topic_scanner=None):
        """Initialize the sync service."""
        self.task_service = task_service
        self.config = config
        self.topic_scanner = topic_scanner
        self.is_running = False
        self.sync_task = None
        self.last_sync_per_user: Dict[int, datetime] = {}
        
        # Track what tasks should exist in database (based on topic reality)
        self.topic_reality: Dict[int, Set[str]] = {}  # user_id -> set of ticket IDs
        
    async def start(self):
        """Start the background sync service."""
        if self.is_running:
            return
        
        self.is_running = True
        self.sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Database sync service started")
    
    async def stop(self):
        """Stop the background sync service."""
        self.is_running = False
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Database sync service stopped")
    
    async def _sync_loop(self):
        """Main sync loop that runs periodically."""
        while self.is_running:
            try:
                # DISABLED: Automatic sync is too aggressive and deletes valid tasks
                # The sync service needs to be redesigned to be more conservative
                # For now, only manual sync via commands is safe
                logger.debug("Sync loop running (automatic sync disabled)")
                
                # Run sync every 30 minutes (but do nothing)
                await asyncio.sleep(30 * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                await asyncio.sleep(5 * 60)
    
    async def _perform_topic_scanner_sync(self):
        """Sync database with topic reality using the topic scanner."""
        try:
            logger.info("🔄 Starting topic scanner-based database sync...")
            
            # Get the application from somewhere - we need to pass it
            # For now, we'll skip this if we don't have access to the application
            if not hasattr(self, 'application'):
                logger.warning("Application not available for topic scanner sync")
                return
            
            # Use topic scanner to sync
            stats = await self.topic_scanner.sync_database_with_topic_reality(self.application)
            
            if stats.get("error"):
                logger.error(f"Topic scanner sync error: {stats['error']}")
                # Alert admins about sync error
                security_service = self.bot_context.bot_data.get('security_alert_service')
                if security_service:
                    await security_service.log_failed_operation(
                        "Database Sync",
                        "Topic scanner sync failed",
                        stats.get("error")
                    )
            else:
                logger.info(f"✅ Topic scanner sync completed: {stats}")
                
        except Exception as e:
            logger.error(f"Error in topic scanner sync: {e}")
            # Alert admins about critical sync failure
            security_service = self.bot_context.bot_data.get('security_alert_service')
            if security_service:
                await security_service.log_failed_operation(
                    "Database Sync",
                    "Critical failure in topic scanner sync",
                    str(e)
                )
    
    async def _perform_reality_sync(self):
        """Sync database with topic reality for all users."""
        try:
            logger.info("Starting reality-based database sync")
            
            total_synced = 0
            total_removed = 0
            
            # Sync each user's tasks with their topic reality
            for user_id, expected_tickets in self.topic_reality.items():
                removed_count = await self._sync_user_with_reality(user_id, expected_tickets)
                if removed_count > 0:
                    total_synced += 1
                    total_removed += removed_count
            
            if total_removed > 0:
                logger.info(f"Reality sync completed: synced {total_synced} users, removed {total_removed} orphaned tasks")
            else:
                logger.debug("Reality sync completed: all databases in sync with topics")
                
        except Exception as e:
            logger.error(f"Error in reality sync: {e}")
    
    async def _sync_user_with_reality(self, user_id: int, expected_tickets: Set[str]) -> int:
        """
        Sync user's database tasks with topic reality.
        Returns number of tasks removed.
        """
        try:
            # Get all user's active tasks from database
            all_user_tasks = await self.task_service.task_repo.get_tasks_by_assignee(user_id)
            active_states = [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.REJECTED]
            active_tasks = [t for t in all_user_tasks if t.state in active_states]
            
            # Find tasks in database that shouldn't exist (not in topic reality)
            db_tickets = {task.ticket for task in active_tasks}
            orphaned_tickets = db_tickets - expected_tickets
            
            # Alert admins if significant mismatch detected
            if len(orphaned_tickets) >= 3:
                security_service = self.bot_context.bot_data.get('security_alert_service')
                if security_service:
                    await security_service.log_failed_operation(
                        "Database Sync",
                        f"Found {len(orphaned_tickets)} orphaned tasks for user {user_id}",
                        f"Tickets: {', '.join(list(orphaned_tickets)[:5])}"
                    )
            
            # Remove orphaned tasks
            removed_count = 0
            for ticket in orphaned_tickets:
                try:
                    await self.task_service.task_repo.db.delete_task(ticket)
                    removed_count += 1
                    logger.info(f"Reality sync: Removed orphaned task {ticket} for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to remove orphaned task {ticket}: {e}")
            
            if removed_count > 0:
                logger.info(f"Reality sync: Cleaned {removed_count} orphaned tasks for user {user_id}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error syncing reality for user {user_id}: {e}")
            return 0
    
    def track_task_created(self, user_id: int, ticket: str):
        """Track that a task was created in the topic."""
        if user_id not in self.topic_reality:
            self.topic_reality[user_id] = set()
        
        self.topic_reality[user_id].add(ticket)
        logger.debug(f"Tracked task creation: {ticket} for user {user_id}")
    
    def track_task_deleted(self, user_id: int, ticket: str):
        """Track that a task was deleted from the topic."""
        if user_id in self.topic_reality:
            self.topic_reality[user_id].discard(ticket)
            logger.debug(f"Tracked task deletion: {ticket} for user {user_id}")
    
    async def sync_user_immediately(self, user_id: int):
        """
        Immediately sync tasks for a specific user with their topic reality.
        """
        try:
            # Don't sync the same user too frequently (max once per 2 minutes for immediate sync)
            last_sync = self.last_sync_per_user.get(user_id)
            if last_sync and (datetime.now() - last_sync).total_seconds() < 120:
                return
            
            # Get expected tickets for this user
            expected_tickets = self.topic_reality.get(user_id, set())
            
            # Sync with reality
            removed_count = await self._sync_user_with_reality(user_id, expected_tickets)
            
            if removed_count > 0:
                logger.info(f"Immediate reality sync: Cleaned {removed_count} orphaned tasks for user {user_id}")
            
            self.last_sync_per_user[user_id] = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in immediate reality sync for user {user_id}: {e}")
    
    async def initialize_reality_from_database(self):
        """
        Initialize topic reality tracking from current database state.
        This helps when the bot restarts - assumes current DB reflects topic reality.
        """
        try:
            logger.info("Initializing topic reality from database...")
            
            # Get all active tasks from database
            all_tasks = await self.task_service.task_repo.db.fetch_all(
                "SELECT ticket, assignee_id FROM tasks WHERE state IN (?, ?, ?, ?)",
                (TaskState.ASSIGNED.value, TaskState.STARTED.value, 
                 TaskState.QA_SUBMITTED.value, TaskState.REJECTED.value)
            )
            
            # Build reality map
            for task in all_tasks:
                user_id = task['assignee_id']
                ticket = task['ticket']
                
                if user_id not in self.topic_reality:
                    self.topic_reality[user_id] = set()
                
                self.topic_reality[user_id].add(ticket)
            
            total_users = len(self.topic_reality)
            total_tasks = sum(len(tickets) for tickets in self.topic_reality.values())
            
            logger.info(f"Initialized topic reality: {total_users} users, {total_tasks} tasks")
            
        except Exception as e:
            logger.error(f"Error initializing topic reality: {e}")
    
    async def auto_recovery_on_startup(self):
        """
        Automatically recover and sync database with likely topic reality on bot startup.
        This runs automatically when bot starts to handle cases where bot was offline.
        """
        try:
            logger.info("🔄 Starting auto-recovery process...")
            
            from datetime import datetime, timedelta
            
            # Get all users with active tasks before recovery
            all_tasks_before = await self.task_service.task_repo.db.fetch_all(
                "SELECT assignee_id, COUNT(*) as task_count FROM tasks WHERE state IN (?, ?, ?, ?) GROUP BY assignee_id",
                (TaskState.ASSIGNED.value, TaskState.STARTED.value, 
                 TaskState.QA_SUBMITTED.value, TaskState.REJECTED.value)
            )
            
            users_before = {task['assignee_id']: task['task_count'] for task in all_tasks_before}
            
            # Run recovery for each user
            total_cleaned_users = 0
            total_removed_tasks = 0
            
            for user_id in users_before.keys():
                removed_count = await self._auto_recovery_for_user(user_id)
                if removed_count > 0:
                    total_cleaned_users += 1
                    total_removed_tasks += removed_count
            
            # Get counts after recovery
            all_tasks_after = await self.task_service.task_repo.db.fetch_all(
                "SELECT assignee_id, COUNT(*) as task_count FROM tasks WHERE state IN (?, ?, ?, ?) GROUP BY assignee_id",
                (TaskState.ASSIGNED.value, TaskState.STARTED.value, 
                 TaskState.QA_SUBMITTED.value, TaskState.REJECTED.value)
            )
            
            users_after = {task['assignee_id']: task['task_count'] for task in all_tasks_after}
            
            if total_removed_tasks > 0:
                logger.info(f"✅ Auto-recovery completed: cleaned {total_cleaned_users} users, removed {total_removed_tasks} stale tasks")
                
                # Log details for each cleaned user
                for user_id in users_before.keys():
                    before_count = users_before.get(user_id, 0)
                    after_count = users_after.get(user_id, 0)
                    if before_count != after_count:
                        logger.info(f"   User {user_id}: {before_count} → {after_count} tasks")
            else:
                logger.info("✅ Auto-recovery completed: database already clean")
            
            # Initialize reality tracking with cleaned database
            await self.initialize_reality_from_database()
            
        except Exception as e:
            logger.error(f"❌ Error in auto-recovery: {e}")
            # Still try to initialize reality tracking even if recovery failed
            try:
                await self.initialize_reality_from_database()
            except Exception as init_error:
                logger.error(f"❌ Error initializing reality tracking: {init_error}")
    
    async def _auto_recovery_for_user(self, user_id: int) -> int:
        """
        Auto-recovery for a specific user - removes likely stale tasks.
        Returns number of tasks removed.
        """
        try:
            from datetime import datetime, timedelta
            
            # Get all user's active tasks
            all_user_tasks = await self.task_service.task_repo.get_tasks_by_assignee(user_id)
            active_states = [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.REJECTED]
            active_tasks = [t for t in all_user_tasks if t.state in active_states]
            
            if len(active_tasks) <= 3:
                # If user has 3 or fewer tasks, assume they're all current
                return 0
            
            # Auto-recovery strategy: Keep only recent tasks
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Keep tasks from today and yesterday (most likely to still exist)
            recent_tasks = [t for t in active_tasks if t.created_at.date() >= yesterday]
            old_tasks = [t for t in active_tasks if t.created_at.date() < yesterday]
            
            # If still too many recent tasks, keep only the 5 most recent
            if len(recent_tasks) > 5:
                sorted_tasks = sorted(recent_tasks, key=lambda t: t.created_at, reverse=True)
                tasks_to_keep = sorted_tasks[:5]
                tasks_to_remove = sorted_tasks[5:] + old_tasks
            else:
                tasks_to_keep = recent_tasks
                tasks_to_remove = old_tasks
            
            # Remove stale tasks
            removed_count = 0
            removed_tickets = []
            for task in tasks_to_remove:
                try:
                    await self.task_service.task_repo.db.delete_task(task.ticket)
                    removed_count += 1
                    removed_tickets.append(task.ticket)
                    logger.debug(f"Auto-recovery: Removed stale task {task.ticket} for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to remove stale task {task.ticket}: {e}")
            
            if removed_count > 0:
                logger.info(f"Auto-recovery: Cleaned {removed_count} stale tasks for user {user_id}: {', '.join(removed_tickets)}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error in auto-recovery for user {user_id}: {e}")
            return 0
    
    def get_user_reality(self, user_id: int) -> Set[str]:
        """Get the expected tickets for a user based on topic reality."""
        return self.topic_reality.get(user_id, set()).copy()
    
    def get_reality_stats(self) -> Dict[str, int]:
        """Get statistics about topic reality tracking."""
        total_users = len(self.topic_reality)
        total_tasks = sum(len(tickets) for tickets in self.topic_reality.values())
        
        return {
            "users": total_users,
            "tasks": total_tasks
        }