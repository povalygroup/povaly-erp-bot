"""Escalation and reminder service for Core Operations issues."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from src.services.issue_service import IssueService
from src.data.models.issue import Issue

logger = logging.getLogger(__name__)


class EscalationService:
    """Service for handling issue escalation and reminders."""
    
    def __init__(self, issue_service: IssueService, bot_context, config, task_service=None):
        """Initialize escalation service."""
        self.issue_service = issue_service
        self.task_service = task_service
        self.bot_context = bot_context
        self.config = config
        self.running = False
        self.escalation_task = None
        self.reminder_task = None
        self.task_escalation_task = None
        
        # Configuration
        self.escalation_hours = 2  # Issue escalation after 2 hours
        self.reminder_hours = 4    # Issue reminder after 4 hours
        self.task_escalation_hours = config.TASK_ESCALATION_HOURS  # Task escalation (default: 72h)
        self.check_interval = 300  # Check every 5 minutes (300 seconds)
    
    async def start(self):
        """Start the escalation and reminder background tasks."""
        if self.running:
            logger.warning("Escalation service is already running")
            return
        
        self.running = True
        logger.info("Starting escalation and reminder service...")
        
        # Start background tasks
        self.escalation_task = asyncio.create_task(self._escalation_loop())
        self.reminder_task = asyncio.create_task(self._reminder_loop())
        
        # Start task escalation if task_service is available
        if self.task_service:
            self.task_escalation_task = asyncio.create_task(self._task_escalation_loop())
        
        logger.info("Escalation and reminder service started")
    
    async def stop(self):
        """Stop the escalation and reminder background tasks."""
        if not self.running:
            return
        
        logger.info("Stopping escalation and reminder service...")
        self.running = False
        
        # Cancel tasks
        if self.escalation_task:
            self.escalation_task.cancel()
            try:
                await self.escalation_task
            except asyncio.CancelledError:
                pass
        
        if self.reminder_task:
            self.reminder_task.cancel()
            try:
                await self.reminder_task
            except asyncio.CancelledError:
                pass
        
        if self.task_escalation_task:
            self.task_escalation_task.cancel()
            try:
                await self.task_escalation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Escalation and reminder service stopped")
    
    async def _escalation_loop(self):
        """Background loop for checking and escalating overdue issues."""
        logger.info("Started escalation monitoring loop")
        
        while self.running:
            try:
                await self._check_overdue_issues()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in escalation loop: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info("Escalation monitoring loop stopped")
    
    async def _reminder_loop(self):
        """Background loop for sending reminders to users with claimed issues."""
        logger.info("Started reminder monitoring loop")
        
        while self.running:
            try:
                await self._check_reminder_issues()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reminder loop: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info("Reminder monitoring loop stopped")
    
    async def _check_overdue_issues(self):
        """Check for overdue issues and escalate them."""
        try:
            # Get overdue issues
            overdue_issues = await self.issue_service.get_overdue_issues(self.escalation_hours)
            
            if not overdue_issues:
                return
            
            logger.info(f"Found {len(overdue_issues)} overdue issues for escalation")
            
            # Log each issue ticket for debugging
            for issue in overdue_issues:
                logger.debug(f"Overdue issue: ticket={issue.ticket}, issue_ticket={issue.issue_ticket}, escalation_sent={issue.escalation_sent}")
            
            for issue in overdue_issues:
                # Only escalate if not already escalated
                success = await self.issue_service.mark_escalated(issue.ticket)
                if success:
                    await self._send_escalation_message(issue)
                else:
                    logger.debug(f"Skipping escalation for {issue.ticket} - already escalated or failed to mark")
                
        except Exception as e:
            logger.error(f"Error checking overdue issues: {e}")
    
    async def _send_escalation_message(self, issue: Issue):
        """Send escalation message to Admin Control Panel."""
        try:
            # Calculate time elapsed
            time_elapsed = datetime.now() - issue.created_at
            hours_elapsed = int(time_elapsed.total_seconds() / 3600)
            
            # Get creator username
            user_repo = self.bot_context.bot_data.get('user_repository')
            creator_username = f"<@{issue.creator_id}>"
            if user_repo:
                creator = await user_repo.get_user(issue.creator_id)
                if creator and creator.username:
                    creator_username = f"@{creator.username}"
            
            # Determine status text and assignee
            if not issue.claimed_by:
                status_text = "UNATTENDED"
                assignee_text = "No one claimed"
            else:
                status_text = "NOT RESOLVED"
                # Get usernames for handlers
                handler_names = []
                for uid in issue.claimed_by:
                    if user_repo:
                        handler = await user_repo.get_user(uid)
                        if handler and handler.username:
                            handler_names.append(f"@{handler.username}")
                        else:
                            handler_names.append(f"<@{uid}>")
                    else:
                        handler_names.append(f"<@{uid}>")
                assignee_text = ", ".join(handler_names)
            
            # Create escalation message
            escalation_msg = f"""🚨 **ISSUE ESCALATION**

[TICKET] {issue.ticket}
[STATUS] {status_text}
[ISSUE] {issue.title}
[ASSIGNEE] {assignee_text}
[TIME_ELAPSED] {hours_elapsed} hours
[PRIORITY] {issue.priority.value}

**Details:**
{issue.details}

**Message:** This issue has not been resolved within the expected time. Immediate attention required.

**Created by:** {creator_username}
**Created at:** {issue.created_at.strftime('%Y-%m-%d %H:%M')}"""
            
            # Send to Admin Control Panel
            sent_msg = await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=escalation_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_ADMIN_CONTROL_PANEL
            )
            
            # Log admin alert
            from src.utils.admin_alert_helper import log_admin_alert
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if db_adapter:
                await log_admin_alert(
                    db_adapter,
                    sent_msg.message_id,
                    self.config.TOPIC_ADMIN_CONTROL_PANEL,
                    "issue_escalation",
                    f"Issue {issue.ticket} - {issue.title}"
                )
            
            logger.info(f"📨 Sent escalation message for issue {issue.ticket} after {hours_elapsed} hours")
            
        except Exception as e:
            logger.error(f"Error sending escalation message for {issue.ticket}: {e}", exc_info=True)
    
    async def _check_reminder_issues(self):
        """Check for issues that need reminders."""
        try:
            # Get issues needing reminders
            reminder_issues = await self.issue_service.get_issues_needing_reminder(self.reminder_hours)
            
            if not reminder_issues:
                return
            
            logger.info(f"Found {len(reminder_issues)} issues needing reminders")
            
            for issue in reminder_issues:
                await self._send_reminder(issue)
                
        except Exception as e:
            logger.error(f"Error checking reminder issues: {e}")
    
    async def _send_reminder(self, issue: Issue):
        """Send reminder to users who claimed an issue."""
        try:
            # Calculate time elapsed since claim
            time_elapsed = datetime.now() - issue.claimed_at
            hours_elapsed = int(time_elapsed.total_seconds() / 3600)
            
            # Send reminder to each user who claimed the issue
            for user_id in issue.claimed_by:
                try:
                    reminder_msg = f"""⏰ **Issue Reminder**

You have an unresolved issue that needs attention:

**Ticket:** {issue.ticket}
**Issue:** {issue.title}
**Priority:** {issue.priority.value}
**Claimed:** {hours_elapsed} hours ago

**Details:**
{issue.details}

Please update the issue status or resolve it if completed.

**Commands:**
• `/issue {issue.ticket}` - View full details
• `/close {issue.ticket}` - Mark as resolved
• React with ❤️ on the original message to resolve"""
                    
                    await self.bot_context.bot.send_message(
                        chat_id=user_id,
                        text=reminder_msg,
                        parse_mode='Markdown'
                    )
                    
                    logger.info(f"Sent reminder to user {user_id} for issue {issue.ticket}")
                    
                except Exception as e:
                    logger.warning(f"Failed to send reminder to user {user_id}: {e}")
            
            # Mark reminder as sent
            await self.issue_service.mark_reminder_sent(issue.ticket)
            
        except Exception as e:
            logger.error(f"Error sending reminder for issue {issue.ticket}: {e}")
    
    async def force_check_escalations(self):
        """Force check for escalations (for testing/manual trigger)."""
        logger.info("Force checking escalations...")
        await self._check_overdue_issues()
    
    async def force_check_reminders(self):
        """Force check for reminders (for testing/manual trigger)."""
        logger.info("Force checking reminders...")
        await self._check_reminder_issues()
    
    async def _task_escalation_loop(self):
        """Background loop for checking and escalating stuck tasks."""
        logger.info("Started task escalation monitoring loop")
        
        while self.running:
            try:
                await self._check_stuck_tasks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task escalation loop: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info("Task escalation monitoring loop stopped")
    
    async def _check_stuck_tasks(self):
        """Check for tasks stuck in ASSIGNED or STARTED state."""
        try:
            from src.data.models.task import TaskState
            
            # Get all tasks in ASSIGNED or STARTED state
            assigned_tasks = await self.task_service.task_repo.get_tasks_by_state(TaskState.ASSIGNED)
            started_tasks = await self.task_service.task_repo.get_tasks_by_state(TaskState.STARTED)
            
            all_tasks = assigned_tasks + started_tasks
            
            if not all_tasks:
                return
            
            now = datetime.now()
            stuck_tasks = []
            
            for task in all_tasks:
                # Calculate time in current state
                if task.state == TaskState.STARTED and task.started_at:
                    time_elapsed = now - task.started_at
                else:
                    time_elapsed = now - task.created_at
                
                hours_elapsed = time_elapsed.total_seconds() / 3600
                
                if hours_elapsed >= self.task_escalation_hours:
                    stuck_tasks.append((task, hours_elapsed))
            
            if not stuck_tasks:
                return
            
            logger.info(f"Found {len(stuck_tasks)} stuck tasks for escalation")
            
            for task, hours_elapsed in stuck_tasks:
                await self._send_task_escalation_alert(task, int(hours_elapsed))
                
        except Exception as e:
            logger.error(f"Error checking stuck tasks: {e}")
    
    async def _send_task_escalation_alert(self, task, hours_elapsed: int):
        """Send task escalation alert to Admin Control Panel and DM to assignee."""
        try:
            # Get assignee info
            user_repo = self.bot_context.bot_data.get('user_repository')
            assignee_name = f"User {task.assignee_id}"
            if user_repo:
                assignee = await user_repo.get_user(task.assignee_id)
                if assignee and assignee.username:
                    assignee_name = f"@{assignee.username}"
            
            # Build link to task message
            from src.utils.link_builder import build_message_link
            task_link = build_message_link(self.config.TELEGRAM_GROUP_ID, task.message_id)
            
            # Send DM to assignee first
            try:
                assignee_msg = f"""⏰ **Task Stuck - Action Required**

**Task:** #{task.ticket}
**State:** {task.state.value.upper()}
**Stuck for:** {hours_elapsed}h

[View Task]({task_link})

Please update status or contact admin if blocked."""
                
                await self.bot_context.bot.send_message(
                    chat_id=task.assignee_id,
                    text=assignee_msg,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info(f"📨 Sent task escalation DM to assignee {task.assignee_id} for {task.ticket}")
            except Exception as e:
                logger.warning(f"Failed to send task escalation DM to assignee {task.assignee_id}: {e}")
            
            # Create compact alert message for Admin Control Panel
            alert_msg = f"""⏰ **Task Stuck**

**Ticket:** #{task.ticket}
**Assignee:** {assignee_name}
**State:** {task.state.value.upper()}
**Stuck for:** {hours_elapsed}h ({hours_elapsed//24}d)
**Brand:** {task.brand}

[View Task]({task_link})"""
            
            # Send to Admin Control Panel
            sent_msg = await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=alert_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_ADMIN_CONTROL_PANEL,
                disable_web_page_preview=True
            )
            
            # Log admin alert
            from src.utils.admin_alert_helper import log_admin_alert
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if db_adapter:
                await log_admin_alert(
                    db_adapter,
                    sent_msg.message_id,
                    self.config.TOPIC_ADMIN_CONTROL_PANEL,
                    "task_escalation",
                    f"Task #{task.ticket} stuck for {hours_elapsed}h"
                )
            
            logger.info(f"📨 Sent task escalation alert to Admin Control Panel for {task.ticket}")
            
        except Exception as e:
            logger.error(f"Error sending task escalation alert for {task.ticket}: {e}")
    
    def get_status(self) -> dict:
        """Get service status."""
        return {
            "running": self.running,
            "escalation_hours": self.escalation_hours,
            "reminder_hours": self.reminder_hours,
            "check_interval": self.check_interval,
            "escalation_task_running": self.escalation_task and not self.escalation_task.done(),
            "reminder_task_running": self.reminder_task and not self.reminder_task.done()
        }