"""Deadline reminder service for task deadline alerts."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from src.data.models.task import Task, TaskState

logger = logging.getLogger(__name__)


class DeadlineReminderService:
    """Service for handling task deadline reminders."""
    
    def __init__(self, bot_context, config, task_service=None):
        """Initialize deadline reminder service."""
        self.bot_context = bot_context
        self.config = config
        self.task_service = task_service
        self.running = False
        self.reminder_task = None
        
        # Configuration
        self.check_interval = 300  # Check every 5 minutes
    
    async def start(self):
        """Start the deadline reminder background task."""
        if self.running:
            logger.warning("Deadline reminder service is already running")
            return
        
        self.running = True
        logger.info("Starting deadline reminder service...")
        
        # Start background task
        self.reminder_task = asyncio.create_task(self._reminder_loop())
        
        logger.info("Deadline reminder service started")
    
    async def stop(self):
        """Stop the deadline reminder background task."""
        if not self.running:
            return
        
        logger.info("Stopping deadline reminder service...")
        self.running = False
        
        # Cancel task
        if self.reminder_task:
            self.reminder_task.cancel()
            try:
                await self.reminder_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Deadline reminder service stopped")
    
    async def _reminder_loop(self):
        """Background loop for checking task deadlines."""
        logger.info("Started deadline reminder monitoring loop")
        
        while self.running:
            try:
                await self._check_deadlines()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in deadline reminder loop: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info("Deadline reminder monitoring loop stopped")
    
    async def _check_deadlines(self):
        """Check for tasks with upcoming or overdue deadlines."""
        try:
            if not self.task_service:
                return
            
            # Get all active tasks
            active_states = [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED]
            all_tasks = []
            
            for state in active_states:
                tasks = await self.task_service.task_repo.get_tasks_by_state(state)
                all_tasks.extend(tasks)
            
            if not all_tasks:
                return
            
            now = datetime.now()
            
            for task in all_tasks:
                if not task.deadline:
                    continue
                
                time_until_deadline = task.deadline - now
                hours_until = time_until_deadline.total_seconds() / 3600
                
                # Check for different deadline scenarios
                if hours_until < 0:
                    # OVERDUE
                    await self._send_overdue_alert(task, abs(hours_until))
                elif hours_until < 1:
                    # 1 HOUR BEFORE
                    await self._send_1hour_reminder(task)
                elif hours_until < 25 and hours_until > 23:
                    # 24 HOURS BEFORE
                    await self._send_24hour_reminder(task)
            
        except Exception as e:
            logger.error(f"Error checking deadlines: {e}")
    
    async def _send_24hour_reminder(self, task: Task):
        """Send 24-hour deadline reminder to assignee."""
        try:
            from src.utils.message_utils import send_auto_delete_dm
            
            hours_left = (task.deadline - datetime.now()).total_seconds() / 3600
            
            # Only send if we haven't sent recently (within last hour)
            if hours_left > 24.5 or hours_left < 23.5:
                return
            
            # Get user repo for username
            user_repo = self.bot_context.bot_data.get('user_repository')
            assignee_name = f"User {task.assignee_id}"
            if user_repo:
                assignee = await user_repo.get_user(task.assignee_id)
                if assignee and assignee.username:
                    assignee_name = f"@{assignee.username}"
            
            # Build link
            from src.utils.link_builder import build_message_link
            task_link = build_message_link(self.config.TELEGRAM_GROUP_ID, task.message_id)
            
            message = f"""⏰ **Deadline Reminder - 24 Hours**

**Task:** #{task.ticket}
**Brand:** {task.brand}
**Deadline:** {task.deadline.strftime('%Y-%m-%d %H:%M')}
**Time Left:** ~24 hours

[📎 View Task]({task_link})

Please start working on this task if you haven't already!"""
            
            await send_auto_delete_dm(
                context=self.bot_context,
                user_id=task.assignee_id,
                text=message,
                delete_after_seconds=300
            )
            
            logger.info(f"📨 Sent 24-hour reminder to user {task.assignee_id} for task {task.ticket}")
            
        except Exception as e:
            logger.error(f"Error sending 24-hour reminder for task {task.ticket}: {e}")
    
    async def _send_1hour_reminder(self, task: Task):
        """Send 1-hour deadline reminder to assignee."""
        try:
            from src.utils.message_utils import send_auto_delete_dm
            
            hours_left = (task.deadline - datetime.now()).total_seconds() / 3600
            
            # Only send if we haven't sent recently (within last 30 minutes)
            if hours_left > 1.5 or hours_left < 0.5:
                return
            
            # Get user repo for username
            user_repo = self.bot_context.bot_data.get('user_repository')
            assignee_name = f"User {task.assignee_id}"
            if user_repo:
                assignee = await user_repo.get_user(task.assignee_id)
                if assignee and assignee.username:
                    assignee_name = f"@{assignee.username}"
            
            # Build link
            from src.utils.link_builder import build_message_link
            task_link = build_message_link(self.config.TELEGRAM_GROUP_ID, task.message_id)
            
            message = f"""🚨 **URGENT - Deadline in 1 Hour!**

**Task:** #{task.ticket}
**Brand:** {task.brand}
**Deadline:** {task.deadline.strftime('%Y-%m-%d %H:%M')}
**Time Left:** ~1 hour

[📎 View Task]({task_link})

⚠️ Complete this task immediately or contact your manager!"""
            
            await send_auto_delete_dm(
                context=self.bot_context,
                user_id=task.assignee_id,
                text=message,
                delete_after_seconds=300
            )
            
            logger.info(f"📨 Sent 1-hour reminder to user {task.assignee_id} for task {task.ticket}")
            
        except Exception as e:
            logger.error(f"Error sending 1-hour reminder for task {task.ticket}: {e}")
    
    async def _send_overdue_alert(self, task: Task, hours_overdue: float):
        """Send overdue alert to assignee and admins."""
        try:
            from src.utils.message_utils import send_auto_delete_dm
            
            # Send to assignee
            from src.utils.link_builder import build_message_link
            task_link = build_message_link(self.config.TELEGRAM_GROUP_ID, task.message_id)
            
            assignee_msg = f"""❌ **OVERDUE - Task Past Deadline!**

**Task:** #{task.ticket}
**Brand:** {task.brand}
**Deadline:** {task.deadline.strftime('%Y-%m-%d %H:%M')}
**Overdue By:** {hours_overdue:.1f} hours

[📎 View Task]({task_link})

⚠️ This task is OVERDUE! Contact your manager immediately!"""
            
            await send_auto_delete_dm(
                context=self.bot_context,
                user_id=task.assignee_id,
                text=assignee_msg,
                delete_after_seconds=600
            )
            
            logger.info(f"📨 Sent overdue alert to user {task.assignee_id} for task {task.ticket}")
            
            # Send to Admin Control Panel
            user_repo = self.bot_context.bot_data.get('user_repository')
            assignee_name = f"User {task.assignee_id}"
            if user_repo:
                assignee = await user_repo.get_user(task.assignee_id)
                if assignee and assignee.username:
                    assignee_name = f"@{assignee.username}"
            
            admin_msg = f"""🚨 **OVERDUE TASK ALERT**

**Task:** #{task.ticket}
**Assignee:** {assignee_name}
**Brand:** {task.brand}
**Deadline:** {task.deadline.strftime('%Y-%m-%d %H:%M')}
**Overdue By:** {hours_overdue:.1f} hours
**Current State:** {task.state.value}

[📎 View Task]({task_link})

Action required: Contact assignee or escalate."""
            
            await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=admin_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_ADMIN_CONTROL_PANEL,
                disable_web_page_preview=True
            )
            
            logger.info(f"📨 Sent overdue alert to Admin Control Panel for task {task.ticket}")
            
        except Exception as e:
            logger.error(f"Error sending overdue alert for task {task.ticket}: {e}")
    
    def get_status(self) -> dict:
        """Get service status."""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "reminder_task_running": self.reminder_task and not self.reminder_task.done()
        }
