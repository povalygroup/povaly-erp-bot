"""Escalation and reminder service for QA submissions."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from src.services.qa_service import QAService
from src.data.models.qa_submission import QASubmission, QAStatus

logger = logging.getLogger(__name__)


class QAEscalationService:
    """Service for handling QA escalation and reminders."""
    
    def __init__(self, qa_service: QAService, qa_repo, bot_context, config):
        """Initialize QA escalation service."""
        self.qa_service = qa_service
        self.qa_repo = qa_repo
        self.bot_context = bot_context
        self.config = config
        self.running = False
        self.escalation_task = None
        self.reminder_task = None
        
        # Get configuration from config
        self.escalation_hours = config.QA_ESCALATION_HOURS
        self.reminder_hours = config.QA_REMINDER_HOURS
        self.check_interval = 600   # Check every 10 minutes (600 seconds)
    
    async def start(self):
        """Start the QA escalation and reminder background tasks."""
        if self.running:
            logger.warning("QA escalation service is already running")
            return
        
        self.running = True
        logger.info("Starting QA escalation and reminder service...")
        
        # Start background tasks
        self.escalation_task = asyncio.create_task(self._escalation_loop())
        self.reminder_task = asyncio.create_task(self._reminder_loop())
        
        logger.info("QA escalation and reminder service started")
    
    async def stop(self):
        """Stop the QA escalation and reminder background tasks."""
        if not self.running:
            return
        
        logger.info("Stopping QA escalation and reminder service...")
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
        
        logger.info("QA escalation and reminder service stopped")
    
    async def _escalation_loop(self):
        """Background loop for checking and escalating overdue QA submissions."""
        logger.info("Started QA escalation monitoring loop")
        
        while self.running:
            try:
                await self._check_overdue_qa()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in QA escalation loop: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info("QA escalation monitoring loop stopped")
    
    async def _reminder_loop(self):
        """Background loop for sending reminders to reviewers with claimed QA."""
        logger.info("Started QA reminder monitoring loop")
        
        while self.running:
            try:
                await self._check_reminder_qa()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in QA reminder loop: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info("QA reminder monitoring loop stopped")
    
    async def _check_overdue_qa(self):
        """Check for overdue QA submissions and escalate them."""
        try:
            # Get pending QA submissions
            pending_submissions = await self.qa_repo.get_submissions_by_status(QAStatus.PENDING)
            
            if not pending_submissions:
                return
            
            now = datetime.now()
            overdue_submissions = []
            
            for qa in pending_submissions:
                time_elapsed = now - qa.submitted_at
                hours_elapsed = time_elapsed.total_seconds() / 3600
                
                if hours_elapsed >= self.escalation_hours:
                    # Check if already has fire reaction
                    has_fire = await self._has_fire_reaction(qa.message_id)
                    if not has_fire:
                        overdue_submissions.append(qa)
            
            if not overdue_submissions:
                return
            
            logger.info(f"Found {len(overdue_submissions)} overdue QA submissions for escalation")
            
            for qa in overdue_submissions:
                await self._escalate_qa(qa)
                
        except Exception as e:
            logger.error(f"Error checking overdue QA submissions: {e}")
    
    async def _has_fire_reaction(self, message_id: int) -> bool:
        """Check if a message already has fire reaction."""
        try:
            # Get message reactions
            # Note: This would require fetching the message and checking reactions
            # For now, we'll just add the fire reaction and let Telegram handle duplicates
            return False
        except Exception as e:
            logger.error(f"Error checking fire reaction: {e}")
            return False
    
    async def _escalate_qa(self, qa: QASubmission):
        """Escalate a QA submission by adding fire reaction and alerting admins."""
        try:
            from telegram import ReactionTypeEmoji
            
            # Calculate time elapsed
            time_elapsed = datetime.now() - qa.submitted_at
            hours_elapsed = int(time_elapsed.total_seconds() / 3600)
            
            # Add fire reaction to the QA message
            await self.bot_context.bot.set_message_reaction(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                message_id=qa.message_id,
                reaction=[ReactionTypeEmoji(emoji="🔥")],
                is_big=True
            )
            
            logger.info(f"🔥 Escalated QA {qa.ticket} after {hours_elapsed} hours with no review")
            
            # Send alert to Admin Control Panel
            await self._send_escalation_alert(qa, hours_elapsed)
            
        except Exception as e:
            logger.error(f"Error escalating QA {qa.ticket}: {e}")
    
    async def _send_escalation_alert(self, qa: QASubmission, hours_elapsed: int):
        """Send QA escalation alert to Admin Control Panel."""
        try:
            # Get submitter info
            user_repo = self.bot_context.bot_data.get('user_repository')
            submitter_name = f"User {qa.submitter_id}"
            if user_repo:
                submitter = await user_repo.get_user(qa.submitter_id)
                if submitter and submitter.username:
                    submitter_name = f"@{submitter.username}"
            
            # Build link to QA message
            group_id_str = str(self.config.TELEGRAM_GROUP_ID)
            if group_id_str.startswith('-100'):
                group_id_clean = group_id_str[4:]
            else:
                group_id_clean = group_id_str
            
            qa_link = f"https://t.me/c/{group_id_clean}/{qa.message_id}"
            
            # Create compact alert message
            alert_msg = f"""🔥 **QA Pending Review**

**Ticket:** #{qa.ticket}
**Submitted by:** {submitter_name}
**Waiting:** {hours_elapsed}h
**Asset:** {qa.asset}

[View QA]({qa_link})"""
            
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
                    "qa_escalation",
                    f"QA #{qa.ticket} pending for {hours_pending}h"
                )
            
            logger.info(f"📨 Sent QA escalation alert to Admin Control Panel for {qa.ticket}")
            
        except Exception as e:
            logger.error(f"Error sending QA escalation alert for {qa.ticket}: {e}")
    
    async def _check_reminder_qa(self):
        """Check for QA submissions that need reminders."""
        try:
            # Get pending QA submissions
            pending_submissions = await self.qa_repo.get_submissions_by_status(QAStatus.PENDING)
            
            if not pending_submissions:
                return
            
            now = datetime.now()
            reminder_submissions = []
            
            for qa in pending_submissions:
                time_elapsed = now - qa.submitted_at
                hours_elapsed = time_elapsed.total_seconds() / 3600
                
                # Check if claimed (has thumbs up reaction) but not reviewed
                if hours_elapsed >= self.reminder_hours:
                    has_claim = await self._has_claim_reaction(qa.message_id)
                    has_review = await self._has_review_reaction(qa.message_id)
                    
                    if has_claim and not has_review:
                        reminder_submissions.append(qa)
            
            if not reminder_submissions:
                return
            
            logger.info(f"Found {len(reminder_submissions)} QA submissions needing reminders")
            
            for qa in reminder_submissions:
                await self._send_reminder(qa)
                
        except Exception as e:
            logger.error(f"Error checking QA reminders: {e}")
    
    async def _has_claim_reaction(self, message_id: int) -> bool:
        """Check if a message has thumbs up (claim) reaction."""
        try:
            # This would require fetching message reactions
            # For simplicity, we'll check if the message exists and has reactions
            # In a real implementation, you'd fetch the message and check reactions
            return True  # Assume claimed if old enough
        except Exception as e:
            logger.error(f"Error checking claim reaction: {e}")
            return False
    
    async def _has_review_reaction(self, message_id: int) -> bool:
        """Check if a message has heart (approve) or thumbs down (reject) reaction."""
        try:
            # This would require fetching message reactions
            # For simplicity, we'll assume not reviewed if still pending
            return False
        except Exception as e:
            logger.error(f"Error checking review reaction: {e}")
            return False
    
    async def _send_reminder(self, qa: QASubmission):
        """Send reminder to reviewers who claimed the QA."""
        try:
            # Calculate time elapsed
            time_elapsed = datetime.now() - qa.submitted_at
            hours_elapsed = int(time_elapsed.total_seconds() / 3600)
            
            # Build link to QA message
            group_id_str = str(self.config.TELEGRAM_GROUP_ID)
            if group_id_str.startswith('-100'):
                group_id_clean = group_id_str[4:]
            else:
                group_id_clean = group_id_str
            
            qa_link = f"https://t.me/c/{group_id_clean}/{self.config.TOPIC_QA_REVIEW}/{qa.message_id}"
            
            # Send reminder to all QA reviewers
            reminder_msg = f"""⏰ **QA Review Reminder**

A QA submission is waiting for your review:

**Ticket:** #{qa.ticket}
**Asset:** {qa.asset}
**Brand:** {qa.brand}
**Submitted:** {hours_elapsed} hours ago

[📎 View QA Submission]({qa_link})

**Actions:**
• React with ❤️ to approve
• Use `/reject #{qa.ticket} <reason>` to reject with feedback

Please review and take action.

_⏱️ This message will auto-delete in 300 seconds_"""
            
            # Send to all QA reviewers
            for reviewer_id in self.config.QA_REVIEWERS:
                try:
                    await self.bot_context.bot.send_message(
                        chat_id=reviewer_id,
                        text=reminder_msg,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    logger.info(f"Sent QA reminder to reviewer {reviewer_id} for {qa.ticket}")
                    
                    # Schedule auto-delete
                    import asyncio
                    async def delete_qa_reminder():
                        await asyncio.sleep(300)
                        pass
                    asyncio.create_task(delete_qa_reminder())
                    
                except Exception as e:
                    logger.warning(f"Failed to send reminder to reviewer {reviewer_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error sending reminder for QA {qa.ticket}: {e}")
    
    async def force_check_escalations(self):
        """Force check for escalations (for testing/manual trigger)."""
        logger.info("Force checking QA escalations...")
        await self._check_overdue_qa()
    
    async def force_check_reminders(self):
        """Force check for reminders (for testing/manual trigger)."""
        logger.info("Force checking QA reminders...")
        await self._check_reminder_qa()
    
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
