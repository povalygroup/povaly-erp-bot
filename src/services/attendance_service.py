"""Attendance service for auto check-out and attendance management."""

import asyncio
import logging
from datetime import datetime, date, time, timedelta
from typing import List

from src.data.repositories.attendance_repository import AttendanceRepository

logger = logging.getLogger(__name__)


class AttendanceService:
    """Service for handling attendance automation."""
    
    def __init__(self, attendance_repo: AttendanceRepository, bot_context, config):
        """Initialize attendance service."""
        self.attendance_repo = attendance_repo
        self.bot_context = bot_context
        self.config = config
        self.running = False
        self.checkout_task = None
        self.late_alert_task = None
        self.late_pattern_task = None
        self.missing_checkin_task = None
        self.daily_summary_task = None
        
        # Configuration
        self.auto_checkout_time = time(18, 0)  # 6:00 PM
        self.late_checkin_time = time(10, 0)  # 10:00 AM
        self.late_alert_time = time(10, 15)  # 10:15 AM
        self.late_pattern_check_time = time(9, 0)  # 9:00 AM - Check weekly patterns
        self.daily_summary_time = time(17, 0)  # 5:00 PM - Daily attendance summary
        
        # Parse missing checkin alert time from config
        missing_time_parts = config.ATTENDANCE_MISSING_CHECKIN_ALERT_TIME.split(':')
        self.missing_checkin_alert_time = time(int(missing_time_parts[0]), int(missing_time_parts[1]))
        
        self.late_checkin_alert_count = config.ATTENDANCE_LATE_CHECKIN_ALERT_COUNT
        self.check_interval = 60  # Check every 1 minute
    
    async def start(self):
        """Start the attendance service background tasks."""
        if self.running:
            logger.warning("Attendance service is already running")
            return
        
        self.running = True
        logger.info("Starting attendance service...")
        
        # Start background tasks
        self.checkout_task = asyncio.create_task(self._auto_checkout_loop())
        self.late_alert_task = asyncio.create_task(self._late_alert_loop())
        self.late_pattern_task = asyncio.create_task(self._late_pattern_loop())
        self.missing_checkin_task = asyncio.create_task(self._missing_checkin_loop())
        self.daily_summary_task = asyncio.create_task(self._daily_summary_loop())
        
        logger.info("Attendance service started")
    
    async def stop(self):
        """Stop the attendance service background tasks."""
        if not self.running:
            return
        
        logger.info("Stopping attendance service...")
        self.running = False
        
        # Cancel tasks
        if self.checkout_task:
            self.checkout_task.cancel()
            try:
                await self.checkout_task
            except asyncio.CancelledError:
                pass
        
        if self.late_alert_task:
            self.late_alert_task.cancel()
            try:
                await self.late_alert_task
            except asyncio.CancelledError:
                pass
        
        if self.late_pattern_task:
            self.late_pattern_task.cancel()
            try:
                await self.late_pattern_task
            except asyncio.CancelledError:
                pass
        
        if self.missing_checkin_task:
            self.missing_checkin_task.cancel()
            try:
                await self.missing_checkin_task
            except asyncio.CancelledError:
                pass
        
        if self.daily_summary_task:
            self.daily_summary_task.cancel()
            try:
                await self.daily_summary_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Attendance service stopped")
    
    async def _auto_checkout_loop(self):
        """Background loop for auto check-out at 6:00 PM."""
        logger.info("Started auto check-out monitoring loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's 6:00 PM (within 1 minute window)
                if (current_time.hour == self.auto_checkout_time.hour and 
                    current_time.minute == self.auto_checkout_time.minute):
                    await self._process_auto_checkouts()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto checkout loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Auto check-out monitoring loop stopped")
    
    async def _late_alert_loop(self):
        """Background loop for late check-in alerts at 10:15 AM."""
        logger.info("Started late check-in alert loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's 10:15 AM (within 1 minute window)
                if (current_time.hour == self.late_alert_time.hour and 
                    current_time.minute == self.late_alert_time.minute):
                    await self._send_late_checkin_alerts()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in late alert loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Late check-in alert loop stopped")
    
    async def _process_auto_checkouts(self):
        """Process auto check-outs for all users who haven't checked out."""
        try:
            today = date.today()
            
            # Get all users from database
            user_repo = self.bot_context.bot_data.get('user_repository')
            if not user_repo:
                logger.warning("User repository not available for auto checkout")
                # Alert admins about this failure
                security_service = self.bot_context.bot_data.get('security_alert_service')
                if security_service:
                    await security_service.log_failed_operation(
                        "Auto Check-out",
                        "User repository not available",
                        "Cannot process auto check-outs without user repository"
                    )
                return
            
            # Get all users
            from src.data.adapters.sqlite_adapter import SQLiteAdapter
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if not isinstance(db_adapter, SQLiteAdapter):
                return
            
            users = await db_adapter.get_all_users()
            
            checkout_count = 0
            failed_checkouts = []
            
            for user in users:
                try:
                    # Check if user has attendance today
                    attendance = await self.attendance_repo.get_attendance(user.user_id, today)
                    
                    if attendance and not attendance.checkout_time:
                        # Auto check-out
                        checkout_time = datetime.now()
                        await self.attendance_repo.update_checkout(
                            user.user_id, 
                            today, 
                            checkout_time, 
                            is_auto=True
                        )
                        
                        # Calculate total hours
                        total_seconds = (checkout_time - attendance.checkin_time).total_seconds()
                        total_hours = total_seconds / 3600
                        
                        # Send DM notification
                        try:
                            checkin_str = attendance.checkin_time.strftime('%I:%M %p')
                            checkout_str = checkout_time.strftime('%I:%M %p')
                            
                            await self.bot_context.bot.send_message(
                                chat_id=user.user_id,
                                text=f"""🏁 **Auto Check-out**

**Check-in:** {checkin_str}
**Check-out:** {checkout_str} (Auto)
**Total Hours:** {total_hours:.1f} hours
**Date:** {today.strftime('%Y-%m-%d')}

Have a great evening!""",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send auto checkout DM to user {user.user_id}: {e}")
                        
                        checkout_count += 1
                        logger.info(f"✅ Auto checked out user {user.user_id} at {checkout_str} ({total_hours:.1f} hours)")
                
                except Exception as e:
                    logger.error(f"Error processing auto checkout for user {user.user_id}: {e}")
                    failed_checkouts.append((user.user_id, str(e)))
            
            if checkout_count > 0:
                logger.info(f"✅ Processed {checkout_count} auto check-outs")
            
            # Alert admins if there were failures
            if failed_checkouts:
                security_service = self.bot_context.bot_data.get('security_alert_service')
                if security_service:
                    failed_list = "\n".join([f"• User {uid}: {err[:50]}" for uid, err in failed_checkouts[:5]])
                    await security_service.log_failed_operation(
                        "Auto Check-out",
                        f"Failed to check out {len(failed_checkouts)} users",
                        failed_list
                    )
                
        except Exception as e:
            logger.error(f"Error in _process_auto_checkouts: {e}", exc_info=True)
            # Alert admins about critical failure
            security_service = self.bot_context.bot_data.get('security_alert_service')
            if security_service:
                await security_service.log_failed_operation(
                    "Auto Check-out",
                    "Critical failure in auto check-out process",
                    str(e)
                )
    
    async def _send_late_checkin_alerts(self):
        """Send alerts for users who haven't checked in by 10:15 AM."""
        try:
            today = date.today()
            
            # Get all users
            user_repo = self.bot_context.bot_data.get('user_repository')
            if not user_repo:
                logger.warning("User repository not available for late alerts")
                return
            
            from src.data.adapters.sqlite_adapter import SQLiteAdapter
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if not isinstance(db_adapter, SQLiteAdapter):
                return
            
            users = await db_adapter.get_all_users()
            
            alert_count = 0
            for user in users:
                try:
                    # Skip if user is on leave
                    if user.is_on_leave:
                        continue
                    
                    # Check if user has checked in today
                    attendance = await self.attendance_repo.get_attendance(user.user_id, today)
                    
                    if not attendance:
                        # Send reminder DM
                        try:
                            await self.bot_context.bot.send_message(
                                chat_id=user.user_id,
                                text=f"""⏰ **Check-in Reminder**

You haven't checked in today yet.

**Time:** {datetime.now().strftime('%I:%M %p')}
**Expected:** Before 10:00 AM

Please use `/checkin` or start your first task to mark attendance.

_Note: Late check-ins are tracked._""",
                                parse_mode='Markdown'
                            )
                            alert_count += 1
                            logger.info(f"📨 Sent late check-in reminder to user {user.user_id}")
                        except Exception as e:
                            logger.warning(f"Failed to send late alert DM to user {user.user_id}: {e}")
                
                except Exception as e:
                    logger.error(f"Error processing late alert for user {user.user_id}: {e}")
            
            if alert_count > 0:
                logger.info(f"📨 Sent {alert_count} late check-in alerts")
                
        except Exception as e:
            logger.error(f"Error in _send_late_checkin_alerts: {e}", exc_info=True)
    
    def get_status(self) -> dict:
        """Get service status."""
        return {
            "running": self.running,
            "auto_checkout_time": self.auto_checkout_time.strftime('%H:%M'),
            "late_alert_time": self.late_alert_time.strftime('%H:%M'),
            "late_pattern_check_time": self.late_pattern_check_time.strftime('%H:%M'),
            "missing_checkin_alert_time": self.missing_checkin_alert_time.strftime('%H:%M'),
            "daily_summary_time": self.daily_summary_time.strftime('%H:%M'),
            "check_interval": self.check_interval,
            "checkout_task_running": self.checkout_task and not self.checkout_task.done(),
            "late_alert_task_running": self.late_alert_task and not self.late_alert_task.done(),
            "late_pattern_task_running": self.late_pattern_task and not self.late_pattern_task.done(),
            "missing_checkin_task_running": self.missing_checkin_task and not self.missing_checkin_task.done(),
            "daily_summary_task_running": self.daily_summary_task and not self.daily_summary_task.done()
        }
    
    async def _missing_checkin_loop(self):
        """Background loop for checking missing check-ins at configured time."""
        logger.info("Started missing check-in monitoring loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's the configured alert time (within 1 minute window)
                if (current_time.hour == self.missing_checkin_alert_time.hour and 
                    current_time.minute == self.missing_checkin_alert_time.minute):
                    await self._check_missing_checkins()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in missing checkin loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Missing check-in monitoring loop stopped")
    
    async def _check_missing_checkins(self):
        """Check for employees who haven't checked in and send admin alert."""
        try:
            today = date.today()
            
            # Get all users
            user_repo = self.bot_context.bot_data.get('user_repository')
            if not user_repo:
                logger.warning("User repository not available for missing checkin check")
                return
            
            from src.data.adapters.sqlite_adapter import SQLiteAdapter
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if not isinstance(db_adapter, SQLiteAdapter):
                return
            
            users = await db_adapter.get_all_users()
            
            missing_users = []
            for user in users:
                try:
                    # Skip if user is on leave
                    if user.is_on_leave:
                        continue
                    
                    # Check if user has checked in today
                    attendance = await self.attendance_repo.get_attendance(user.user_id, today)
                    
                    if not attendance:
                        missing_users.append(user)
                
                except Exception as e:
                    logger.error(f"Error checking missing checkin for user {user.user_id}: {e}")
            
            if missing_users:
                # Send single consolidated alert to Admin Control Panel
                await self._send_missing_checkin_alert(missing_users)
                logger.info(f"📨 Sent missing check-in alert for {len(missing_users)} employees")
                
        except Exception as e:
            logger.error(f"Error in _check_missing_checkins: {e}", exc_info=True)
    
    async def _send_missing_checkin_alert(self, missing_users):
        """Send consolidated missing check-in alert to Admin Control Panel."""
        try:
            current_time = datetime.now().strftime('%I:%M %p')
            
            # Build compact alert message
            alert_msg = f"""📭 **Missing Check-ins**

**Time:** {current_time}
**Count:** {len(missing_users)} employees

**Employees:**
"""
            
            # List all missing employees
            for user in missing_users:
                username = f"@{user.username}" if user.username else f"User {user.user_id}"
                alert_msg += f"• {username} (ID: {user.user_id})\n"
            
            alert_msg += f"\n_These employees have not checked in yet today._"
            
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
                    "missing_checkin",
                    f"{len(missing_users)} employees missing check-in"
                )
            
            logger.info(f"📨 Sent missing check-in alert to Admin Control Panel for {len(missing_users)} users")
            
        except Exception as e:
            logger.error(f"Error sending missing checkin alert: {e}")
    
    async def _late_pattern_loop(self):
        """Background loop for checking late check-in patterns at 9:00 AM."""
        logger.info("Started late check-in pattern monitoring loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's 9:00 AM (within 1 minute window)
                if (current_time.hour == self.late_pattern_check_time.hour and 
                    current_time.minute == self.late_pattern_check_time.minute):
                    await self._check_late_patterns()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in late pattern loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Late check-in pattern monitoring loop stopped")
    
    async def _check_late_patterns(self):
        """Check for employees with excessive late check-ins in the past week."""
        try:
            today = date.today()
            week_ago = today - timedelta(days=7)
            
            # Get all users
            user_repo = self.bot_context.bot_data.get('user_repository')
            if not user_repo:
                logger.warning("User repository not available for late pattern check")
                return
            
            from src.data.adapters.sqlite_adapter import SQLiteAdapter
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if not isinstance(db_adapter, SQLiteAdapter):
                return
            
            users = await db_adapter.get_all_users()
            
            alert_count = 0
            for user in users:
                try:
                    # Get late check-ins for the past week
                    late_checkins = await self.attendance_repo.get_late_checkins(user.user_id, week_ago, today)
                    
                    if len(late_checkins) >= self.late_checkin_alert_count:
                        # Send alert to Admin Control Panel
                        await self._send_late_pattern_alert(user, late_checkins)
                        alert_count += 1
                
                except Exception as e:
                    logger.error(f"Error checking late pattern for user {user.user_id}: {e}")
            
            if alert_count > 0:
                logger.info(f"📨 Sent {alert_count} late check-in pattern alerts")
                
        except Exception as e:
            logger.error(f"Error in _check_late_patterns: {e}", exc_info=True)
    
    async def _send_late_pattern_alert(self, user, late_checkins):
        """Send late check-in pattern alert to Admin Control Panel."""
        try:
            username = f"@{user.username}" if user.username else f"User {user.user_id}"
            
            # Build compact alert message
            alert_msg = f"""⚠️ **Late Check-in Pattern**

**Employee:** {username}
**User ID:** {user.user_id}
**Late Check-ins:** {len(late_checkins)} in past 7 days

**Recent Late Check-ins:**
"""
            
            # Show last 5 late check-ins
            for attendance in sorted(late_checkins, key=lambda x: x.date, reverse=True)[:5]:
                checkin_time = attendance.checkin_time.strftime('%I:%M %p')
                alert_msg += f"• {attendance.date.strftime('%Y-%m-%d')} - {checkin_time}\n"
            
            if len(late_checkins) > 5:
                alert_msg += f"\n_+{len(late_checkins) - 5} more late check-ins_"
            
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
                    "late_checkin_pattern",
                    f"{user.username} - {len(late_checkins)} late check-ins in 7 days"
                )
            
            logger.info(f"📨 Sent late pattern alert to Admin Control Panel for user {user.user_id}")
            
        except Exception as e:
            logger.error(f"Error sending late pattern alert for user {user.user_id}: {e}")
    
    async def _daily_summary_loop(self):
        """Background loop for sending daily attendance summary at 5:00 PM."""
        logger.info("Started daily attendance summary loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's 5:00 PM (within 1 minute window)
                if (current_time.hour == self.daily_summary_time.hour and 
                    current_time.minute == self.daily_summary_time.minute):
                    await self._send_daily_attendance_summary()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in daily summary loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Daily attendance summary loop stopped")
    
    async def _send_daily_attendance_summary(self):
        """Send daily attendance summary to configured admin DM recipients."""
        try:
            today = date.today()
            
            # Get all attendance records for today
            from src.data.adapters.sqlite_adapter import SQLiteAdapter
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if not isinstance(db_adapter, SQLiteAdapter):
                return
            
            # Get all users
            user_repo = self.bot_context.bot_data.get('user_repository')
            if not user_repo:
                logger.warning("User repository not available for daily summary")
                return
            
            users = await db_adapter.get_all_users()
            
            total_users = len(users)
            checked_in = 0
            late_checkins = 0
            missing_checkins = 0
            
            for user in users:
                try:
                    # Skip if user is on leave
                    if user.is_on_leave:
                        total_users -= 1
                        continue
                    
                    attendance = await self.attendance_repo.get_attendance(user.user_id, today)
                    
                    if attendance:
                        checked_in += 1
                        if attendance.is_late:
                            late_checkins += 1
                    else:
                        missing_checkins += 1
                
                except Exception as e:
                    logger.error(f"Error processing user {user.user_id} for daily summary: {e}")
            
            # Build summary message
            summary_msg = f"""📊 **Daily Attendance Summary**

**Date:** {today.strftime('%Y-%m-%d')}
**Time:** {datetime.now().strftime('%I:%M %p')}

**Overview:**
• Total Employees: {total_users}
• Checked In: {checked_in}
• Late Check-ins: {late_checkins}
• Missing: {missing_checkins}

[View Details in Admin Panel]"""
            
            # Send to configured admin DM recipients
            admin_recipients = self.config.ADMIN_DM_RECIPIENTS
            
            if not admin_recipients:
                logger.info("No admin DM recipients configured for daily summary")
                return
            
            sent_count = 0
            for admin_id in admin_recipients:
                try:
                    await self.bot_context.bot.send_message(
                        chat_id=admin_id,
                        text=summary_msg,
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                    logger.info(f"📨 Sent daily attendance summary to admin {admin_id}")
                except Exception as e:
                    logger.warning(f"Failed to send daily summary to admin {admin_id}: {e}")
            
            if sent_count > 0:
                logger.info(f"✅ Sent daily attendance summary to {sent_count} admins")
                
        except Exception as e:
            logger.error(f"Error in _send_daily_attendance_summary: {e}", exc_info=True)
