"""Service for tracking security events and unauthorized access attempts."""

import logging
from datetime import datetime, date
from typing import Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class SecurityAlertService:
    """Service for tracking security events and alerting admins."""
    
    def __init__(self, bot_context, config):
        """Initialize security alert service."""
        self.bot_context = bot_context
        self.config = config
        
        # Track unauthorized attempts per user per day: {user_id: {date: count}}
        self.daily_attempts: Dict[int, Dict[date, int]] = defaultdict(lambda: defaultdict(int))
        
        # Configuration
        self.alert_threshold = 3  # Alert after 3 unauthorized attempts in a day
    
    async def log_unauthorized_access(self, user_id: int, username: str, command: str, reason: str):
        """
        Log unauthorized access attempt and alert if threshold exceeded.
        
        Args:
            user_id: User who attempted access
            username: Username of the user
            command: Command or action attempted
            reason: Why access was denied
        """
        try:
            today = date.today()
            self.daily_attempts[user_id][today] += 1
            attempt_count = self.daily_attempts[user_id][today]
            
            logger.warning(f"Unauthorized access attempt by user {user_id} ({username}): {command} - {reason} (attempt #{attempt_count} today)")
            
            # Alert admins if threshold exceeded
            if attempt_count >= self.alert_threshold:
                await self._send_security_alert(user_id, username, command, reason, attempt_count)
            
        except Exception as e:
            logger.error(f"Error logging unauthorized access for user {user_id}: {e}")
    
    async def _send_security_alert(self, user_id: int, username: str, command: str, reason: str, attempt_count: int):
        """Send security alert to Admin Control Panel."""
        try:
            user_display = f"@{username}" if username else f"User {user_id}"
            
            # Build compact alert message
            alert_msg = f"""🔒 **Unauthorized Access Attempts**

**Employee:** {user_display}
**User ID:** {user_id}
**Attempts Today:** {attempt_count}

**Latest Attempt:**
• Command: `{command}`
• Reason: {reason}
• Time: {datetime.now().strftime('%I:%M %p')}

_Multiple unauthorized access attempts detected._"""
            
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
                    "unauthorized_access",
                    f"User {user_id} - {attempt_count} unauthorized attempts"
                )
            
            logger.info(f"📨 Sent security alert to Admin Control Panel for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending security alert for user {user_id}: {e}")
    
    async def log_failed_operation(self, operation: str, details: str, error: str = None):
        """
        Log failed system operations (auto-checkout, archive, etc).
        
        Args:
            operation: Name of the operation that failed
            details: Details about what failed
            error: Error message if available
        """
        try:
            logger.error(f"Failed operation: {operation} - {details} - Error: {error}")
            
            # Send alert to Admin Control Panel
            await self._send_operation_failure_alert(operation, details, error)
            
        except Exception as e:
            logger.error(f"Error logging failed operation: {e}")
    
    async def _send_operation_failure_alert(self, operation: str, details: str, error: str = None):
        """Send operation failure alert to Admin Control Panel."""
        try:
            # Build compact alert message
            alert_msg = f"""⚠️ **System Operation Failed**

**Operation:** {operation}
**Time:** {datetime.now().strftime('%I:%M %p')}

**Details:**
{details}"""
            
            if error:
                # Truncate long error messages
                error_display = error[:200] + "..." if len(error) > 200 else error
                alert_msg += f"\n\n**Error:**\n`{error_display}`"
            
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
                    "failed_operation",
                    f"{operation} failed"
                )
            
            logger.info(f"📨 Sent operation failure alert to Admin Control Panel: {operation}")
            
        except Exception as e:
            logger.error(f"Error sending operation failure alert: {e}")
    
    def reset_daily_counts(self):
        """Reset unauthorized attempt counts (called daily)."""
        today = date.today()
        
        # Remove old dates
        for user_id in list(self.daily_attempts.keys()):
            for attempt_date in list(self.daily_attempts[user_id].keys()):
                if attempt_date < today:
                    del self.daily_attempts[user_id][attempt_date]
            
            # Clean up empty user entries
            if not self.daily_attempts[user_id]:
                del self.daily_attempts[user_id]
        
        logger.info("Reset daily unauthorized attempt counts")
