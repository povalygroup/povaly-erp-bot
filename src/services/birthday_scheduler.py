"""Birthday Scheduler - Schedules birthday wishes and reminders."""

import logging
import asyncio
from datetime import datetime, time

logger = logging.getLogger(__name__)


class BirthdayScheduler:
    """Scheduler for birthday wishes and reminders."""
    
    def __init__(self, birthday_service, config, application):
        """Initialize birthday scheduler."""
        self.birthday_service = birthday_service
        self.config = config
        self.application = application
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start the birthday scheduler."""
        if self.running:
            logger.warning("Birthday scheduler already running")
            return
        
        self.running = True
        
        # Parse times from config
        wish_time = self._parse_time(self.config.BIRTHDAY_CHECK_TIME)  # e.g., "09:00"
        reminder_time = self._parse_time(self.config.BIRTHDAY_REMINDER_TIME)  # e.g., "18:00"
        
        # Start birthday wishes scheduler
        wish_task = asyncio.create_task(
            self._schedule_daily_task(
                wish_time,
                self._send_birthday_wishes,
                "Birthday Wishes"
            )
        )
        self.tasks.append(wish_task)
        
        # Start birthday reminders scheduler
        reminder_task = asyncio.create_task(
            self._schedule_daily_task(
                reminder_time,
                self._send_birthday_reminders,
                "Birthday Reminders"
            )
        )
        self.tasks.append(reminder_task)
        
        logger.info(f"Birthday scheduler started: Wishes at {wish_time}, Reminders at {reminder_time}")
    
    async def stop(self):
        """Stop the birthday scheduler."""
        self.running = False
        for task in self.tasks:
            task.cancel()
        self.tasks.clear()
        logger.info("Birthday scheduler stopped")
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string (HH:MM) to time object."""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour=hour, minute=minute)
        except:
            logger.error(f"Invalid time format: {time_str}, using default 09:00")
            return time(hour=9, minute=0)
    
    async def _schedule_daily_task(self, target_time: time, task_func, task_name: str):
        """Schedule a task to run daily at a specific time."""
        while self.running:
            try:
                # Calculate seconds until next run
                now = datetime.now()
                target_datetime = datetime.combine(now.date(), target_time)
                
                # If target time has passed today, schedule for tomorrow
                if target_datetime <= now:
                    from datetime import timedelta
                    target_datetime += timedelta(days=1)
                
                seconds_until = (target_datetime - now).total_seconds()
                
                logger.info(f"{task_name}: Next run in {seconds_until/3600:.1f} hours at {target_datetime}")
                
                # Wait until target time
                await asyncio.sleep(seconds_until)
                
                # Run the task
                if self.running:
                    logger.info(f"⏰ Running {task_name}...")
                    await task_func()
                
            except asyncio.CancelledError:
                logger.info(f"{task_name} scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in {task_name} scheduler: {e}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)
    
    async def _send_birthday_wishes(self):
        """Send birthday wishes for today's birthdays."""
        try:
            count = await self.birthday_service.check_and_send_birthday_wishes(
                self.application
            )
            logger.info(f"✅ Birthday wishes sent: {count}")
        except Exception as e:
            logger.error(f"Error sending birthday wishes: {e}")
    
    async def _send_birthday_reminders(self):
        """Send birthday reminders for tomorrow's birthdays."""
        try:
            count = await self.birthday_service.send_birthday_reminders(
                self.application
            )
            logger.info(f"✅ Birthday reminders sent: {count}")
        except Exception as e:
            logger.error(f"Error sending birthday reminders: {e}")
