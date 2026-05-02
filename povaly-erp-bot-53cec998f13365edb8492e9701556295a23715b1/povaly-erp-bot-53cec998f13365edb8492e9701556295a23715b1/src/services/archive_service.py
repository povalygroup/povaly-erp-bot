"""Archive service for automatic task archiving after completion."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from src.data.models.task import Task, TaskState
from src.services.task_service import TaskService

logger = logging.getLogger(__name__)


class ArchiveService:
    """Service for handling automatic task archiving."""
    
    def __init__(self, task_service: TaskService, bot_context, config):
        """Initialize archive service."""
        self.task_service = task_service
        self.bot_context = bot_context
        self.config = config
        self.running = False
        self.archive_task = None
        self.reminder_task = None
        
        # Configuration
        self.reminder_hours = 12  # Remind assignee after 12 hours if not marked complete
        self.archive_delay_hours = 24  # Archive after 24 hours if both conditions met
        self.check_interval = 600  # Check every 10 minutes (600 seconds)
    
    async def start(self):
        """Start the archive service background tasks."""
        if self.running:
            logger.warning("Archive service is already running")
            return
        
        self.running = True
        logger.info("Starting archive service...")
        
        # Start background tasks
        self.archive_task = asyncio.create_task(self._archive_loop())
        self.reminder_task = asyncio.create_task(self._reminder_loop())
        
        logger.info("Archive service started")
    
    async def stop(self):
        """Stop the archive service background tasks."""
        if not self.running:
            return
        
        logger.info("Stopping archive service...")
        self.running = False
        
        # Cancel tasks
        if self.archive_task:
            self.archive_task.cancel()
            try:
                await self.archive_task
            except asyncio.CancelledError:
                pass
        
        if self.reminder_task:
            self.reminder_task.cancel()
            try:
                await self.reminder_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Archive service stopped")
    
    async def _archive_loop(self):
        """Background loop for checking and archiving completed tasks."""
        logger.info("Started archive monitoring loop")
        
        while self.running:
            try:
                await self._check_and_archive_tasks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in archive loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Archive monitoring loop stopped")
    
    async def _reminder_loop(self):
        """Background loop for reminding assignees to mark tasks complete."""
        logger.info("Started completion reminder loop")
        
        while self.running:
            try:
                await self._check_and_remind_assignees()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reminder loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Completion reminder loop stopped")
    
    async def _check_and_archive_tasks(self):
        """Check for tasks ready to archive and archive them."""
        try:
            # Get all approved tasks
            all_tasks = await self.task_service.task_repo.get_all_tasks()
            approved_tasks = [t for t in all_tasks if t.state == TaskState.APPROVED]
            
            if not approved_tasks:
                return
            
            logger.debug(f"Found {len(approved_tasks)} approved tasks to check for archiving")
            
            for task in approved_tasks:
                # Check if task has assignee love reaction (completion confirmation)
                has_completion = await self._has_assignee_love_reaction(task)
                
                if has_completion:
                    # Check if enough time has passed since approval
                    if task.qa_submitted_at:
                        time_since_approval = datetime.now() - task.qa_submitted_at
                        hours_since_approval = time_since_approval.total_seconds() / 3600
                        
                        if hours_since_approval >= self.archive_delay_hours:
                            await self._archive_task(task)
                    else:
                        # No QA timestamp, archive immediately if has completion reaction
                        await self._archive_task(task)
                        
        except Exception as e:
            logger.error(f"Error checking tasks for archiving: {e}", exc_info=True)
    
    async def _check_and_remind_assignees(self):
        """Check for approved tasks without assignee completion and send reminders."""
        try:
            # Get all approved tasks
            all_tasks = await self.task_service.task_repo.get_all_tasks()
            approved_tasks = [t for t in all_tasks if t.state == TaskState.APPROVED]
            
            if not approved_tasks:
                return
            
            now = datetime.now()
            tasks_needing_reminder = []
            
            for task in approved_tasks:
                # Check if task has assignee love reaction
                has_completion = await self._has_assignee_love_reaction(task)
                
                if not has_completion and task.qa_submitted_at:
                    # Check if enough time has passed since approval
                    time_since_approval = now - task.qa_submitted_at
                    hours_since_approval = time_since_approval.total_seconds() / 3600
                    
                    if hours_since_approval >= self.reminder_hours:
                        tasks_needing_reminder.append(task)
            
            if not tasks_needing_reminder:
                return
            
            # Group tasks by assignee
            tasks_by_assignee = {}
            for task in tasks_needing_reminder:
                if task.assignee_id not in tasks_by_assignee:
                    tasks_by_assignee[task.assignee_id] = []
                tasks_by_assignee[task.assignee_id].append(task)
            
            logger.info(f"Found {len(tasks_needing_reminder)} tasks needing completion reminder")
            
            # Send reminders to assignees
            for assignee_id, tasks in tasks_by_assignee.items():
                await self._send_completion_reminder(assignee_id, tasks)
                
        except Exception as e:
            logger.error(f"Error checking completion reminders: {e}", exc_info=True)
    
    async def _has_assignee_love_reaction(self, task: Task) -> bool:
        """Check if the task message has a love reaction from the assignee."""
        try:
            # Get the task message
            message = await self.bot_context.bot.forward_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                from_chat_id=self.config.TELEGRAM_GROUP_ID,
                message_id=task.message_id
            )
            
            # Delete the forwarded message immediately
            await message.delete()
            
            # Check reactions on original message
            # Note: We need to fetch the message to check reactions
            # This is a limitation - we'll track reactions in database instead
            
            # For now, check if there's a reaction record in database
            reactions = await self.task_service.task_repo.get_task_reactions(task.ticket)
            
            # Check if assignee has reacted with ❤️
            for reaction in reactions:
                if reaction.get('user_id') == task.assignee_id and reaction.get('emoji') == '❤️':
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking assignee love reaction for {task.ticket}: {e}")
            return False
    
    async def _archive_task(self, task: Task):
        """Archive a completed task."""
        try:
            logger.info(f"📦 Archiving task {task.ticket}")
            
            # Get the original task message
            try:
                # Forward the task message to Archive topic
                archived_msg = await self.bot_context.bot.forward_message(
                    chat_id=self.config.TELEGRAM_GROUP_ID,
                    from_chat_id=self.config.TELEGRAM_GROUP_ID,
                    message_id=task.message_id,
                    message_thread_id=self.config.TOPIC_ARCHIVE
                )
                
                logger.info(f"Forwarded task {task.ticket} to Archive topic")
                
                # Add archive header
                archive_header = f"""📦 **ARCHIVED TASK**

**Ticket:** #{task.ticket}
**Assignee:** {task.assignee_id}
**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Status:** QA Approved & Confirmed Complete

---"""
                
                await self.bot_context.bot.send_message(
                    chat_id=self.config.TELEGRAM_GROUP_ID,
                    text=archive_header,
                    parse_mode='Markdown',
                    message_thread_id=self.config.TOPIC_ARCHIVE,
                    reply_to_message_id=archived_msg.message_id
                )
                
            except Exception as e:
                logger.warning(f"Failed to forward task to archive: {e}")
                # Alert admins about archive failure
                security_service = self.bot_context.bot_data.get('security_alert_service')
                if security_service:
                    await security_service.log_failed_operation(
                        "Task Archive",
                        f"Failed to forward task {task.ticket} to Archive topic",
                        str(e)
                    )
                raise  # Re-raise to prevent marking as archived if forward failed
            
            # Update task state to ARCHIVED
            await self.task_service.task_repo.update_task_state(
                task.ticket,
                TaskState.ARCHIVED,
                datetime.now()
            )
            
            logger.info(f"✅ Task {task.ticket} archived successfully")
            
            # Send confirmation to assignee
            try:
                user_repo = self.bot_context.bot_data.get('user_repository')
                assignee_username = "there"
                if user_repo:
                    assignee = await user_repo.get_user(task.assignee_id)
                    if assignee and assignee.username:
                        assignee_username = f"@{assignee.username}"
                
                await self.bot_context.bot.send_message(
                    chat_id=task.assignee_id,
                    text=f"""✅ **Task Archived**

Congratulations! Your task **#{task.ticket}** has been archived.

**Status:** Completed & Approved
**Archived:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

Great work on completing this task!""",
                    parse_mode='Markdown'
                )
                logger.info(f"Sent archive confirmation to assignee {task.assignee_id}")
            except Exception as e:
                logger.warning(f"Failed to send archive confirmation: {e}")
            
            # Delete original task message from Task Allocation topic
            try:
                await self.bot_context.bot.delete_message(
                    chat_id=self.config.TELEGRAM_GROUP_ID,
                    message_id=task.message_id
                )
                logger.info(f"Deleted original task message {task.message_id}")
            except Exception as e:
                logger.warning(f"Failed to delete original task message: {e}")
                
        except Exception as e:
            logger.error(f"Error archiving task {task.ticket}: {e}", exc_info=True)
            # Alert admins about critical archive failure
            security_service = self.bot_context.bot_data.get('security_alert_service')
            if security_service:
                await security_service.log_failed_operation(
                    "Task Archive",
                    f"Critical failure archiving task {task.ticket}",
                    str(e)
                )
    
    async def _send_completion_reminder(self, assignee_id: int, tasks: List[Task]):
        """Send reminder to assignee to mark tasks as complete."""
        try:
            # Build task list
            task_list = []
            for task in tasks:
                time_since_approval = datetime.now() - task.qa_submitted_at
                hours_since_approval = int(time_since_approval.total_seconds() / 3600)
                
                # Build link to task message
                group_id_str = str(self.config.TELEGRAM_GROUP_ID)
                if group_id_str.startswith('-100'):
                    group_id_clean = group_id_str[4:]
                else:
                    group_id_clean = group_id_str
                
                task_link = f"https://t.me/c/{group_id_clean}/{self.config.TOPIC_TASK_ALLOCATION}/{task.message_id}"
                
                task_list.append(f"• [#{task.ticket}]({task_link}) - Approved {hours_since_approval}h ago")
            
            # Build reminder message
            reminder_msg = f"""⏰ **Task Completion Reminder**

Your QA has been approved for the following task{'s' if len(tasks) > 1 else ''}:

{chr(10).join(task_list)}

**Action Required:**
React with ❤️ on your task message in Task Allocation to confirm completion.

This will archive the task and mark it as fully complete.

_Note: Tasks will be auto-archived after 24 hours of approval._"""
            
            await self.bot_context.bot.send_message(
                chat_id=assignee_id,
                text=reminder_msg,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            logger.info(f"Sent completion reminder to assignee {assignee_id} for {len(tasks)} task(s)")
            
        except Exception as e:
            logger.error(f"Error sending completion reminder to {assignee_id}: {e}", exc_info=True)
    
    async def force_check_archives(self):
        """Force check for archiving (for testing/manual trigger)."""
        logger.info("Force checking for tasks to archive...")
        await self._check_and_archive_tasks()
    
    async def force_check_reminders(self):
        """Force check for reminders (for testing/manual trigger)."""
        logger.info("Force checking for completion reminders...")
        await self._check_and_remind_assignees()
    
    def get_status(self) -> dict:
        """Get service status."""
        return {
            "running": self.running,
            "reminder_hours": self.reminder_hours,
            "archive_delay_hours": self.archive_delay_hours,
            "check_interval": self.check_interval,
            "archive_task_running": self.archive_task and not self.archive_task.done(),
            "reminder_task_running": self.reminder_task and not self.reminder_task.done()
        }
