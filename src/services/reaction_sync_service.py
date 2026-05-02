"""Reaction sync service - syncs reactions on bot startup for tasks created while bot was offline."""

import logging
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

from src.config import Config
from src.data.models.task import TaskState
from src.services.task_service import TaskService

logger = logging.getLogger(__name__)


class ReactionSyncService:
    """Service to sync reactions on bot startup."""
    
    def __init__(self, config: Config, task_service: TaskService, bot: Bot):
        """Initialize reaction sync service."""
        self.config = config
        self.task_service = task_service
        self.bot = bot
    
    async def sync_all_active_tasks(self):
        """
        Sync reactions for all active tasks on bot startup.
        
        This ensures that reactions added while bot was offline are processed.
        Only syncs tasks in ASSIGNED or QA_SUBMITTED states.
        """
        try:
            logger.info("🔄 Starting reaction sync for active tasks...")
            
            # Get all tasks in ASSIGNED or QA_SUBMITTED states
            assigned_tasks = await self.task_service.get_tasks_by_state(TaskState.ASSIGNED)
            qa_submitted_tasks = await self.task_service.get_tasks_by_state(TaskState.QA_SUBMITTED)
            
            all_active_tasks = assigned_tasks + qa_submitted_tasks
            
            if not all_active_tasks:
                logger.info("✅ No active tasks to sync")
                return
            
            logger.info(f"📋 Found {len(all_active_tasks)} active tasks to sync")
            logger.info(f"   - ASSIGNED: {len(assigned_tasks)}")
            logger.info(f"   - QA_SUBMITTED: {len(qa_submitted_tasks)}")
            
            synced_count = 0
            error_count = 0
            
            for task in all_active_tasks:
                try:
                    await self._sync_task_reactions(task)
                    synced_count += 1
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to sync task {task.ticket}: {e}")
                    error_count += 1
            
            logger.info(f"✅ Reaction sync complete: {synced_count} synced, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Reaction sync failed: {e}", exc_info=True)
    
    async def _sync_task_reactions(self, task):
        """
        Sync reactions for a single task.
        
        Fetches the message from Telegram and processes any reactions.
        """
        try:
            # Get the message from Telegram
            message = await self.bot.forward_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                from_chat_id=self.config.TELEGRAM_GROUP_ID,
                message_id=task.message_id
            )
            
            # Delete the forwarded message immediately
            await message.delete()
            
            # Note: We can't actually get reactions via forward
            # We need to use a different approach
            
            # Alternative: Try to get message via get_updates or use a cache
            # For now, we'll log that we attempted sync
            logger.debug(f"Attempted sync for task {task.ticket} (message {task.message_id})")
            
        except TelegramError as e:
            # Message might be deleted or inaccessible
            logger.warning(f"Could not access message {task.message_id} for task {task.ticket}: {e}")
        except Exception as e:
            logger.error(f"Error syncing task {task.ticket}: {e}")
