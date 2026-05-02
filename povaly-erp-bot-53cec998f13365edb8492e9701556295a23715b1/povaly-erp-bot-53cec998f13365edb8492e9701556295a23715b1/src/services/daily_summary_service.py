"""Daily summary service for admin notifications."""

import asyncio
import logging
from datetime import datetime, date, time, timedelta
from typing import List

logger = logging.getLogger(__name__)


class DailySummaryService:
    """Service for sending daily summaries and digests to admins."""
    
    def __init__(self, bot_context, config, task_service=None, issue_service=None, qa_service=None):
        """Initialize daily summary service."""
        self.bot_context = bot_context
        self.config = config
        self.task_service = task_service
        self.issue_service = issue_service
        self.qa_service = qa_service
        self.running = False
        self.escalation_digest_task = None
        self.weekly_summary_task = None
        self.daily_carryover_task = None
        
        # Configuration
        self.escalation_digest_time = time(9, 0)  # 9:00 AM
        self.weekly_summary_time = time(9, 0)  # Monday 9:00 AM
        
        # Daily carryover summary at midnight (configurable)
        self.daily_carryover_time = time(config.DAILY_SUMMARY_HOUR, config.DAILY_SUMMARY_MINUTE)
        
        self.check_interval = 60  # Check every 1 minute
    
    async def start(self):
        """Start the daily summary service background tasks."""
        if self.running:
            logger.warning("Daily summary service is already running")
            return
        
        self.running = True
        logger.info("Starting daily summary service...")
        
        # Start background tasks
        self.escalation_digest_task = asyncio.create_task(self._escalation_digest_loop())
        self.weekly_summary_task = asyncio.create_task(self._weekly_summary_loop())
        self.daily_carryover_task = asyncio.create_task(self._daily_carryover_loop())
        
        logger.info("Daily summary service started")
    
    async def stop(self):
        """Stop the daily summary service background tasks."""
        if not self.running:
            return
        
        logger.info("Stopping daily summary service...")
        self.running = False
        
        # Cancel tasks
        if self.escalation_digest_task:
            self.escalation_digest_task.cancel()
            try:
                await self.escalation_digest_task
            except asyncio.CancelledError:
                pass
        
        if self.weekly_summary_task:
            self.weekly_summary_task.cancel()
            try:
                await self.weekly_summary_task
            except asyncio.CancelledError:
                pass
        
        if self.daily_carryover_task:
            self.daily_carryover_task.cancel()
            try:
                await self.daily_carryover_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Daily summary service stopped")
    
    async def _escalation_digest_loop(self):
        """Background loop for sending critical escalation digest at 9:00 AM."""
        logger.info("Started escalation digest loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's 9:00 AM (within 1 minute window)
                if (current_time.hour == self.escalation_digest_time.hour and 
                    current_time.minute == self.escalation_digest_time.minute):
                    await self._send_escalation_digest()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in escalation digest loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Escalation digest loop stopped")
    
    async def _send_escalation_digest(self):
        """Send daily escalation digest to configured admin DM recipients."""
        try:
            # Get escalated items from yesterday
            yesterday = date.today() - timedelta(days=1)
            
            # Count stuck tasks
            stuck_tasks_count = 0
            if self.task_service:
                try:
                    from src.data.models.task import TaskState
                    assigned_tasks = await self.task_service.task_repo.get_tasks_by_state(TaskState.ASSIGNED)
                    started_tasks = await self.task_service.task_repo.get_tasks_by_state(TaskState.STARTED)
                    
                    now = datetime.now()
                    task_escalation_hours = self.config.TASK_ESCALATION_HOURS
                    
                    for task in assigned_tasks + started_tasks:
                        if task.state == TaskState.STARTED and task.started_at:
                            time_elapsed = now - task.started_at
                        else:
                            time_elapsed = now - task.created_at
                        
                        hours_elapsed = time_elapsed.total_seconds() / 3600
                        if hours_elapsed >= task_escalation_hours:
                            stuck_tasks_count += 1
                except Exception as e:
                    logger.error(f"Error counting stuck tasks: {e}")
            
            # Count pending QAs
            pending_qas_count = 0
            if self.qa_service:
                try:
                    pending_qas = await self.qa_service.get_pending_submissions()
                    pending_qas_count = len(pending_qas)
                except Exception as e:
                    logger.error(f"Error counting pending QAs: {e}")
            
            # Count unresolved issues
            unresolved_issues_count = 0
            if self.issue_service:
                try:
                    open_issues = await self.issue_service.get_open_issues()
                    unresolved_issues_count = len(open_issues)
                except Exception as e:
                    logger.error(f"Error counting unresolved issues: {e}")
            
            # Only send if there are escalations
            total_escalations = stuck_tasks_count + pending_qas_count + unresolved_issues_count
            
            if total_escalations == 0:
                logger.info("No escalations to report in daily digest")
                return
            
            # Build digest message
            digest_msg = f"""🚨 **Critical Escalation Digest**

**Date:** {date.today().strftime('%Y-%m-%d')}
**Time:** {datetime.now().strftime('%I:%M %p')}

**Pending Items:**
• Stuck Tasks: {stuck_tasks_count}
• Pending QAs: {pending_qas_count}
• Unresolved Issues: {unresolved_issues_count}

**Total:** {total_escalations} items need attention

[View Admin Control Panel for details]"""
            
            # Send to configured admin DM recipients
            admin_recipients = self.config.ADMIN_DM_RECIPIENTS
            
            if not admin_recipients:
                logger.info("No admin DM recipients configured for escalation digest")
                return
            
            sent_count = 0
            for admin_id in admin_recipients:
                try:
                    await self.bot_context.bot.send_message(
                        chat_id=admin_id,
                        text=digest_msg,
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                    logger.info(f"📨 Sent escalation digest to admin {admin_id}")
                except Exception as e:
                    logger.warning(f"Failed to send escalation digest to admin {admin_id}: {e}")
            
            if sent_count > 0:
                logger.info(f"✅ Sent escalation digest to {sent_count} admins")
                
        except Exception as e:
            logger.error(f"Error in _send_escalation_digest: {e}", exc_info=True)
    
    async def _weekly_summary_loop(self):
        """Background loop for sending weekly performance summary on Monday at 9:00 AM."""
        logger.info("Started weekly performance summary loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's Monday 9:00 AM (within 1 minute window)
                if (now.weekday() == 0 and  # Monday
                    current_time.hour == self.weekly_summary_time.hour and 
                    current_time.minute == self.weekly_summary_time.minute):
                    await self._send_weekly_performance_summary()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in weekly summary loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Weekly performance summary loop stopped")
    
    async def _send_weekly_performance_summary(self):
        """Send weekly performance summary to managers."""
        try:
            # Get last week's date range (Monday to Sunday)
            today = date.today()
            last_monday = today - timedelta(days=today.weekday() + 7)
            last_sunday = last_monday + timedelta(days=6)
            
            # Count completed tasks
            completed_tasks_count = 0
            if self.task_service:
                try:
                    from src.data.models.task import TaskState
                    # Get all approved tasks (completed)
                    approved_tasks = await self.task_service.task_repo.get_tasks_by_state(TaskState.APPROVED)
                    
                    # Filter by last week
                    for task in approved_tasks:
                        if task.updated_at and last_monday <= task.updated_at.date() <= last_sunday:
                            completed_tasks_count += 1
                except Exception as e:
                    logger.error(f"Error counting completed tasks: {e}")
            
            # Count approved QAs
            approved_qas_count = 0
            if self.qa_service:
                try:
                    from src.data.models.qa_submission import QAStatus
                    # This would need a method to get QAs by status and date range
                    # For now, we'll skip detailed counting
                    approved_qas_count = 0  # Placeholder
                except Exception as e:
                    logger.error(f"Error counting approved QAs: {e}")
            
            # Count resolved issues
            resolved_issues_count = 0
            if self.issue_service:
                try:
                    # This would need a method to get resolved issues by date range
                    # For now, we'll skip detailed counting
                    resolved_issues_count = 0  # Placeholder
                except Exception as e:
                    logger.error(f"Error counting resolved issues: {e}")
            
            # Build summary message
            summary_msg = f"""📊 **Weekly Performance Summary**

**Week:** {last_monday.strftime('%Y-%m-%d')} to {last_sunday.strftime('%Y-%m-%d')}
**Report Date:** {today.strftime('%Y-%m-%d')}

**Completed Work:**
• Tasks Completed: {completed_tasks_count}
• QAs Approved: {approved_qas_count}
• Issues Resolved: {resolved_issues_count}

[View detailed reports in Admin Panel]"""
            
            # Send to managers
            manager_ids = self.config.MANAGERS
            
            if not manager_ids:
                logger.info("No managers configured for weekly summary")
                return
            
            sent_count = 0
            for manager_id in manager_ids:
                try:
                    await self.bot_context.bot.send_message(
                        chat_id=manager_id,
                        text=summary_msg,
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                    logger.info(f"📨 Sent weekly performance summary to manager {manager_id}")
                except Exception as e:
                    logger.warning(f"Failed to send weekly summary to manager {manager_id}: {e}")
            
            if sent_count > 0:
                logger.info(f"✅ Sent weekly performance summary to {sent_count} managers")
                
        except Exception as e:
            logger.error(f"Error in _send_weekly_performance_summary: {e}", exc_info=True)
    
    async def _daily_carryover_loop(self):
        """Background loop for sending daily carryover summary at midnight."""
        logger.info("Started daily carryover summary loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's the configured time (default midnight)
                if (current_time.hour == self.daily_carryover_time.hour and 
                    current_time.minute == self.daily_carryover_time.minute):
                    await self._send_daily_carryover_summary()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in daily carryover loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Daily carryover summary loop stopped")
    
    async def _send_daily_carryover_summary(self):
        """Send daily carryover summary to relevant topics."""
        try:
            today = date.today()
            
            # 1. TASK ALLOCATION - Carryover tasks
            await self._send_task_carryover_summary()
            
            # 2. CORE OPERATIONS - Unresolved issues
            await self._send_issue_carryover_summary()
            
            # 3. QA REVIEW - Pending QA submissions
            await self._send_qa_carryover_summary()
            
            # 4. ADMIN CONTROL PANEL - Unresolved alerts
            await self._send_admin_panel_carryover_summary()
            
            logger.info(f"✅ Sent daily carryover summaries to all topics")
            
        except Exception as e:
            logger.error(f"Error in _send_daily_carryover_summary: {e}", exc_info=True)
    
    async def _send_task_carryover_summary(self):
        """Send task carryover summary to TOPIC_TASK_ALLOCATION."""
        try:
            if not self.task_service:
                return
            
            from src.data.models.task import TaskState
            
            # Get carryover tasks (not completed)
            assigned_tasks = await self.task_service.task_repo.get_tasks_by_state(TaskState.ASSIGNED)
            started_tasks = await self.task_service.task_repo.get_tasks_by_state(TaskState.STARTED)
            qa_submitted_tasks = await self.task_service.task_repo.get_tasks_by_state(TaskState.QA_SUBMITTED)
            rejected_tasks = await self.task_service.task_repo.get_tasks_by_state(TaskState.REJECTED)
            
            total_carryover = len(assigned_tasks) + len(started_tasks) + len(qa_submitted_tasks) + len(rejected_tasks)
            
            if total_carryover == 0:
                summary_msg = f"""🌅 **DAILY TASK SUMMARY**

**Date:** {date.today().strftime('%A, %B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **No Carryover Tasks**

All tasks from yesterday are completed!
Great work team! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            else:
                summary_msg = f"""🌅 **DAILY TASK SUMMARY**

**Date:** {date.today().strftime('%A, %B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📋 Carryover Tasks: {total_carryover}**

**ASSIGNED** ({len(assigned_tasks)}):
"""
                for task in assigned_tasks[:5]:  # Show first 5
                    summary_msg += f"• #{task.ticket} - Assignee: {task.assignee_id}\n"
                if len(assigned_tasks) > 5:
                    summary_msg += f"  _+{len(assigned_tasks) - 5} more..._\n"
                
                summary_msg += f"\n**STARTED** ({len(started_tasks)}):\n"
                for task in started_tasks[:5]:
                    summary_msg += f"• #{task.ticket} - Assignee: {task.assignee_id}\n"
                if len(started_tasks) > 5:
                    summary_msg += f"  _+{len(started_tasks) - 5} more..._\n"
                
                summary_msg += f"\n**QA SUBMITTED** ({len(qa_submitted_tasks)}):\n"
                for task in qa_submitted_tasks[:5]:
                    summary_msg += f"• #{task.ticket} - Assignee: {task.assignee_id}\n"
                if len(qa_submitted_tasks) > 5:
                    summary_msg += f"  _+{len(qa_submitted_tasks) - 5} more..._\n"
                
                summary_msg += f"\n**REJECTED** ({len(rejected_tasks)}):\n"
                for task in rejected_tasks[:5]:
                    summary_msg += f"• #{task.ticket} - Assignee: {task.assignee_id}\n"
                if len(rejected_tasks) > 5:
                    summary_msg += f"  _+{len(rejected_tasks) - 5} more..._\n"
                
                summary_msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                summary_msg += "**Action Required:**\n"
                summary_msg += "• ASSIGNED → React 👍 to start\n"
                summary_msg += "• STARTED → Submit for QA when done\n"
                summary_msg += "• QA SUBMITTED → Reviewers please check\n"
                summary_msg += "• REJECTED → Fix and resubmit"
            
            # Send to TOPIC_TASK_ALLOCATION
            await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=summary_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_TASK_ALLOCATION
            )
            
            logger.info(f"✅ Sent task carryover summary to TOPIC_TASK_ALLOCATION")
            
        except Exception as e:
            logger.error(f"Error sending task carryover summary: {e}", exc_info=True)
    
    async def _send_issue_carryover_summary(self):
        """Send issue carryover summary to TOPIC_CORE_OPERATIONS."""
        try:
            if not self.issue_service:
                return
            
            # Get unresolved issues
            open_issues = await self.issue_service.get_open_issues()
            
            if len(open_issues) == 0:
                summary_msg = f"""🌅 **DAILY ISSUE SUMMARY**

**Date:** {date.today().strftime('%A, %B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **No Open Issues**

All issues are resolved! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            else:
                summary_msg = f"""🌅 **DAILY ISSUE SUMMARY**

**Date:** {date.today().strftime('%A, %B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⚠️ Open Issues: {len(open_issues)}**

"""
                for issue in open_issues[:10]:  # Show first 10
                    claimed_status = f"Claimed by {len(issue.claimed_by)}" if issue.claimed_by else "Unclaimed"
                    summary_msg += f"• {issue.issue_ticket} - {issue.title}\n"
                    summary_msg += f"  Status: {claimed_status} | Priority: {issue.priority.value}\n"
                
                if len(open_issues) > 10:
                    summary_msg += f"\n_+{len(open_issues) - 10} more issues..._\n"
                
                summary_msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                summary_msg += "**Action Required:**\n"
                summary_msg += "• React 👍 to claim an issue\n"
                summary_msg += "• React ❤️ to mark as resolved\n"
                summary_msg += "• React 👎 to reject as invalid"
            
            # Send to TOPIC_CORE_OPERATIONS
            await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=summary_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_CORE_OPERATIONS
            )
            
            logger.info(f"✅ Sent issue carryover summary to TOPIC_CORE_OPERATIONS")
            
        except Exception as e:
            logger.error(f"Error sending issue carryover summary: {e}", exc_info=True)
    
    async def _send_qa_carryover_summary(self):
        """Send QA carryover summary to TOPIC_QA_REVIEW."""
        try:
            if not self.qa_service:
                return
            
            # Get pending QA submissions
            pending_qas = await self.qa_service.get_pending_submissions()
            
            if len(pending_qas) == 0:
                summary_msg = f"""🌅 **DAILY QA SUMMARY**

**Date:** {date.today().strftime('%A, %B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **No Pending QA Reviews**

All QA submissions are reviewed! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            else:
                summary_msg = f"""🌅 **DAILY QA SUMMARY**

**Date:** {date.today().strftime('%A, %B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🔍 Pending QA Reviews: {len(pending_qas)}**

"""
                for qa in pending_qas[:10]:  # Show first 10
                    time_pending = datetime.now() - qa.submitted_at
                    hours_pending = int(time_pending.total_seconds() / 3600)
                    summary_msg += f"• #{qa.ticket} - {qa.brand}\n"
                    summary_msg += f"  Asset: {qa.asset} | Pending: {hours_pending}h\n"
                
                if len(pending_qas) > 10:
                    summary_msg += f"\n_+{len(pending_qas) - 10} more QA submissions..._\n"
                
                summary_msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                summary_msg += "**Action Required:**\n"
                summary_msg += "• React ❤️ to approve\n"
                summary_msg += "• Use `/reject #ticket <reason>` to reject"
            
            # Send to TOPIC_QA_REVIEW
            await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=summary_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_QA_REVIEW
            )
            
            logger.info(f"✅ Sent QA carryover summary to TOPIC_QA_REVIEW")
            
        except Exception as e:
            logger.error(f"Error sending QA carryover summary: {e}", exc_info=True)
    
    async def _send_admin_panel_carryover_summary(self):
        """Send Admin Control Panel carryover summary."""
        try:
            from src.data.repositories.admin_alert_repository import AdminAlertRepository
            
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if not db_adapter:
                return
            
            admin_alert_repo = AdminAlertRepository(db_adapter)
            
            # Get unresolved alerts (no ❤️ reaction)
            unresolved_alerts = await admin_alert_repo.get_unresolved_alerts()
            
            if len(unresolved_alerts) == 0:
                summary_msg = f"""🌅 **DAILY ADMIN PANEL SUMMARY**

**Date:** {date.today().strftime('%A, %B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **No Unresolved Alerts**

All alerts have been handled! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            else:
                # Group by alert type
                from collections import defaultdict
                alerts_by_type = defaultdict(list)
                
                for alert in unresolved_alerts:
                    alerts_by_type[alert.alert_type].append(alert)
                
                summary_msg = f"""🌅 **DAILY ADMIN PANEL SUMMARY**

**Date:** {date.today().strftime('%A, %B %d, %Y')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**⚠️ Unresolved Alerts: {len(unresolved_alerts)}**

"""
                for alert_type, alerts in alerts_by_type.items():
                    # Format alert type name
                    type_name = alert_type.replace('_', ' ').title()
                    summary_msg += f"\n**{type_name}** ({len(alerts)}):\n"
                    
                    for alert in alerts[:5]:  # Show first 5 of each type
                        ack_status = "👍 Ack" if alert.acknowledged else "⚪ New"
                        age_hours = int((datetime.now() - alert.created_at).total_seconds() / 3600)
                        summary_msg += f"• {ack_status} | {age_hours}h ago\n"
                    
                    if len(alerts) > 5:
                        summary_msg += f"  _+{len(alerts) - 5} more..._\n"
                
                summary_msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                summary_msg += "**Action Required:**\n"
                summary_msg += "• React 👍 to acknowledge alert\n"
                summary_msg += "• React ❤️ to mark as resolved\n"
                summary_msg += "• Resolved alerts won't appear in next summary"
            
            # Send to TOPIC_ADMIN_CONTROL_PANEL
            await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=summary_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_ADMIN_CONTROL_PANEL
            )
            
            logger.info(f"✅ Sent admin panel carryover summary to TOPIC_ADMIN_CONTROL_PANEL")
            
        except Exception as e:
            logger.error(f"Error sending admin panel carryover summary: {e}", exc_info=True)
    
    async def send_manual_summary(self):
        """Manually trigger daily carryover summary (for /dailysummary command)."""
        await self._send_daily_carryover_summary()
    
    def get_status(self) -> dict:
        """Get service status."""
        return {
            "running": self.running,
            "escalation_digest_time": self.escalation_digest_time.strftime('%H:%M'),
            "weekly_summary_time": self.weekly_summary_time.strftime('%H:%M'),
            "daily_carryover_time": self.daily_carryover_time.strftime('%H:%M'),
            "check_interval": self.check_interval,
            "escalation_digest_task_running": self.escalation_digest_task and not self.escalation_digest_task.done(),
            "weekly_summary_task_running": self.weekly_summary_task and not self.weekly_summary_task.done(),
            "daily_carryover_task_running": self.daily_carryover_task and not self.daily_carryover_task.done()
        }
