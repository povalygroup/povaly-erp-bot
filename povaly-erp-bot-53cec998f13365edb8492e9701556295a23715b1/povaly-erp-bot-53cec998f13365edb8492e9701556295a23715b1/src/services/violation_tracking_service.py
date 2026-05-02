"""Service for tracking format violations and alerting admins."""

import logging
from datetime import datetime, date
from typing import Dict, List
from collections import defaultdict

from src.core.violation_detector import ViolationDetector, Violation

logger = logging.getLogger(__name__)


class ViolationTrackingService:
    """Service for tracking user format violations and sending alerts."""
    
    def __init__(self, bot_context, config):
        """Initialize violation tracking service."""
        self.bot_context = bot_context
        self.config = config
        self.violation_detector = ViolationDetector(config)
        
        # Track violations per user per day: {user_id: {date: count}}
        self.daily_violations: Dict[int, Dict[date, int]] = defaultdict(lambda: defaultdict(int))
        
        # Configuration
        self.alert_threshold = config.VIOLATION_ALERT_THRESHOLD
    
    async def check_and_handle_violations(self, user_id: int, username: str, text: str, topic_id: int) -> bool:
        """
        Check message for violations and handle appropriately.
        Returns True if violations found, False otherwise.
        """
        try:
            # Detect violations based on topic
            violations = []
            
            if topic_id == self.config.TOPIC_TASK_ALLOCATION:
                violations = self.violation_detector.detect_task_allocation_violations(text, user_id)
            elif topic_id == self.config.TOPIC_QA_REVIEW:
                violations = self.violation_detector.detect_qa_submission_violations(text)
            
            if not violations:
                return False
            
            # Track violation
            today = date.today()
            self.daily_violations[user_id][today] += 1
            violation_count = self.daily_violations[user_id][today]
            
            logger.info(f"Format violation detected for user {user_id}: {violation_count} violations today")
            
            # Handle based on count
            if violation_count == 1:
                # First violation: Send helpful DM
                await self._send_first_violation_dm(user_id, username, violations, topic_id)
            elif violation_count == 2:
                # Second violation: Send warning DM
                await self._send_second_violation_dm(user_id, username, violations, topic_id)
            elif violation_count >= self.alert_threshold:
                # Third+ violation: Alert admins
                await self._send_admin_alert(user_id, username, violations, violation_count, topic_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling violations for user {user_id}: {e}")
            return False
    
    async def _send_first_violation_dm(self, user_id: int, username: str, violations: List[Violation], topic_id: int):
        """Send helpful DM for first violation."""
        try:
            topic_name = self._get_topic_name(topic_id)
            
            message = f"""💡 **Format Help**

Hi! I noticed your message in **{topic_name}** doesn't match the required format.

**Issues found:**
"""
            
            for v in violations:
                message += f"• {v.message}\n"
                message += f"  💡 {v.suggestion}\n\n"
            
            message += "**Need help?** Check the pinned message in the topic for examples.\n\n"
            message += "_This is a friendly reminder to help you format messages correctly._"
            
            await self.bot_context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Sent first violation DM to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending first violation DM to user {user_id}: {e}")
    
    async def _send_second_violation_dm(self, user_id: int, username: str, violations: List[Violation], topic_id: int):
        """Send warning DM for second violation."""
        try:
            topic_name = self._get_topic_name(topic_id)
            
            message = f"""⚠️ **Format Warning**

This is your **2nd format issue** today in **{topic_name}**.

**Current issues:**
"""
            
            for v in violations:
                message += f"• {v.message}\n"
                message += f"  💡 {v.suggestion}\n\n"
            
            message += "**Please review the format guidelines carefully.**\n\n"
            message += "_One more violation today will alert administrators._"
            
            await self.bot_context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Sent second violation DM to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending second violation DM to user {user_id}: {e}")
    
    async def _send_admin_alert(self, user_id: int, username: str, violations: List[Violation], count: int, topic_id: int):
        """Send alert to Admin Control Panel for repeated violations."""
        try:
            topic_name = self._get_topic_name(topic_id)
            user_display = f"@{username}" if username else f"User {user_id}"
            
            # Build compact alert message
            alert_msg = f"""📝 **Repeated Format Violations**

**Employee:** {user_display}
**User ID:** {user_id}
**Topic:** {topic_name}
**Violations Today:** {count}

**Latest Issues:**
"""
            
            for v in violations:
                alert_msg += f"• {v.message}\n"
            
            # Send to Admin Control Panel
            sent_msg = await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=alert_msg,
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
                    "format_violation",
                    f"User {user_id} - {violation_count} violations today"
                )
            
            logger.info(f"📨 Sent format violation alert to Admin Control Panel for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending admin alert for user {user_id}: {e}")
    
    def _get_topic_name(self, topic_id: int) -> str:
        """Get human-readable topic name."""
        if topic_id == self.config.TOPIC_TASK_ALLOCATION:
            return "Task Allocation"
        elif topic_id == self.config.TOPIC_QA_REVIEW:
            return "QA Review"
        elif topic_id == self.config.TOPIC_CORE_OPERATIONS:
            return "Core Operations"
        else:
            return f"Topic {topic_id}"
    
    def reset_daily_counts(self):
        """Reset violation counts (called daily)."""
        today = date.today()
        
        # Remove old dates
        for user_id in list(self.daily_violations.keys()):
            for violation_date in list(self.daily_violations[user_id].keys()):
                if violation_date < today:
                    del self.daily_violations[user_id][violation_date]
            
            # Clean up empty user entries
            if not self.daily_violations[user_id]:
                del self.daily_violations[user_id]
        
        logger.info("Reset daily violation counts")
