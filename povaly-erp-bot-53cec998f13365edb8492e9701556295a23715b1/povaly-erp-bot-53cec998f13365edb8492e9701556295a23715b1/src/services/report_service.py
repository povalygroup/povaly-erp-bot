"""Report service for generating employee performance reports."""

import asyncio
import logging
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating and sending performance reports."""
    
    def __init__(self, bot_context, config, task_service=None, issue_service=None, qa_service=None, attendance_service=None):
        """Initialize report service."""
        self.bot_context = bot_context
        self.config = config
        self.task_service = task_service
        self.issue_service = issue_service
        self.qa_service = qa_service
        self.attendance_service = attendance_service
        self.running = False
        self.daily_report_task = None
        self.weekly_report_task = None
        self.monthly_report_task = None
        self.performance_report_task = None
        
        # Configuration - Parse report times from config
        daily_time_parts = config.DAILY_REPORT_TIME.split(':')
        self.daily_report_time = time(int(daily_time_parts[0]), int(daily_time_parts[1]))
        
        weekly_time_parts = config.WEEKLY_REPORT_TIME.split(':')
        self.weekly_report_time = time(int(weekly_time_parts[0]), int(weekly_time_parts[1]))
        self.weekly_report_day = config.WEEKLY_REPORT_DAY  # e.g., "Sunday"
        
        # Monthly report on 1st of month at same time as weekly
        self.monthly_report_time = self.weekly_report_time
        
        # Performance report - weekly on Monday at 10:00 AM
        self.performance_report_time = time(10, 0)
        self.performance_report_day = "Monday"
        
        self.check_interval = 60  # Check every 1 minute
    
    async def start(self):
        """Start the report service background tasks."""
        if self.running:
            logger.warning("Report service is already running")
            return
        
        self.running = True
        logger.info("Starting report service...")
        
        # Start background tasks
        self.daily_report_task = asyncio.create_task(self._daily_report_loop())
        self.weekly_report_task = asyncio.create_task(self._weekly_report_loop())
        self.monthly_report_task = asyncio.create_task(self._monthly_report_loop())
        self.performance_report_task = asyncio.create_task(self._performance_report_loop())
        
        logger.info("Report service started")
    
    async def stop(self):
        """Stop the report service background tasks."""
        if not self.running:
            return
        
        logger.info("Stopping report service...")
        self.running = False
        
        # Cancel tasks
        if self.daily_report_task:
            self.daily_report_task.cancel()
            try:
                await self.daily_report_task
            except asyncio.CancelledError:
                pass
        
        if self.weekly_report_task:
            self.weekly_report_task.cancel()
            try:
                await self.weekly_report_task
            except asyncio.CancelledError:
                pass
        
        if self.monthly_report_task:
            self.monthly_report_task.cancel()
            try:
                await self.monthly_report_task
            except asyncio.CancelledError:
                pass
        
        if self.performance_report_task:
            self.performance_report_task.cancel()
            try:
                await self.performance_report_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Report service stopped")
    
    async def _daily_report_loop(self):
        """Background loop for sending daily reports."""
        logger.info("Started daily report loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's the configured daily report time
                if (current_time.hour == self.daily_report_time.hour and 
                    current_time.minute == self.daily_report_time.minute):
                    await self._send_daily_report()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in daily report loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Daily report loop stopped")
    
    async def _weekly_report_loop(self):
        """Background loop for sending weekly reports."""
        logger.info("Started weekly report loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Map day names to weekday numbers (0=Monday, 6=Sunday)
                day_map = {
                    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                    "Friday": 4, "Saturday": 5, "Sunday": 6
                }
                
                target_weekday = day_map.get(self.weekly_report_day, 6)  # Default to Sunday
                
                # Check if it's the configured day and time
                if (now.weekday() == target_weekday and
                    current_time.hour == self.weekly_report_time.hour and 
                    current_time.minute == self.weekly_report_time.minute):
                    await self._send_weekly_report()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in weekly report loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Weekly report loop stopped")
    
    async def _monthly_report_loop(self):
        """Background loop for sending monthly reports."""
        logger.info("Started monthly report loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Check if it's the 1st of the month at the configured time
                if (now.day == 1 and
                    current_time.hour == self.monthly_report_time.hour and 
                    current_time.minute == self.monthly_report_time.minute):
                    await self._send_monthly_report()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monthly report loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Monthly report loop stopped")
    
    async def _send_daily_report(self):
        """Send daily employee performance report to TOPIC_DAILY_SYNC."""
        try:
            today = date.today()
            
            # Get all users
            user_repo = self.bot_context.bot_data.get('user_repository')
            if not user_repo:
                logger.warning("User repository not available for daily report")
                return
            
            from src.data.adapters.sqlite_adapter import SQLiteAdapter
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if not isinstance(db_adapter, SQLiteAdapter):
                return
            
            users = await db_adapter.get_all_users()
            
            # Collect employee data
            employee_data = []
            
            for user in users:
                try:
                    # Get attendance
                    from src.data.repositories.attendance_repository import AttendanceRepository
                    attendance_repo = AttendanceRepository(db_adapter)
                    attendance = await attendance_repo.get_attendance(user.user_id, today)
                    
                    # Get tasks completed today
                    tasks_completed = 0
                    if self.task_service:
                        from src.data.models.task import TaskState
                        all_tasks = await self.task_service.task_repo.get_tasks_by_assignee(user.user_id)
                        for task in all_tasks:
                            if task.updated_at and task.updated_at.date() == today and task.state == TaskState.APPROVED:
                                tasks_completed += 1
                    
                    # Get QA submissions today
                    qa_submitted = 0
                    if self.qa_service:
                        # Would need a method to get QA by date
                        qa_submitted = 0  # Placeholder
                    
                    # Get issues resolved today
                    issues_resolved = 0
                    if self.issue_service:
                        # Would need a method to get resolved issues by date
                        issues_resolved = 0  # Placeholder
                    
                    # Build employee summary
                    username = f"@{user.username}" if user.username else f"User {user.user_id}"
                    
                    if attendance:
                        checkin = attendance.checkin_time.strftime('%I:%M %p')
                        checkout = attendance.checkout_time.strftime('%I:%M %p') if attendance.checkout_time else "Not yet"
                        status = "⚠️ Late" if attendance.is_late else "✅ On-time"
                        hours = f"{attendance.total_hours:.1f}h" if attendance.total_hours else "N/A"
                    else:
                        checkin = "❌ Absent"
                        checkout = "N/A"
                        status = "❌ Absent"
                        hours = "0h"
                    
                    employee_data.append({
                        'username': username,
                        'checkin': checkin,
                        'checkout': checkout,
                        'status': status,
                        'hours': hours,
                        'tasks': tasks_completed,
                        'qa': qa_submitted,
                        'issues': issues_resolved
                    })
                
                except Exception as e:
                    logger.error(f"Error collecting data for user {user.user_id}: {e}")
            
            # Build report message
            report_msg = f"""📊 **DAILY EMPLOYEE REPORT**

**Date:** {today.strftime('%A, %B %d, %Y')}
**Generated:** {datetime.now().strftime('%I:%M %p')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            
            for emp in employee_data:
                report_msg += f"""**{emp['username']}**
├ Check-in: {emp['checkin']} {emp['status']}
├ Check-out: {emp['checkout']}
├ Hours: {emp['hours']}
├ Tasks: {emp['tasks']} completed
├ QA: {emp['qa']} submitted
└ Issues: {emp['issues']} resolved

"""
            
            report_msg += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Summary:**
• Total Employees: {len(employee_data)}
• Present: {sum(1 for e in employee_data if e['checkin'] != '❌ Absent')}
• Absent: {sum(1 for e in employee_data if e['checkin'] == '❌ Absent')}
• Late: {sum(1 for e in employee_data if '⚠️ Late' in e['status'])}
• Total Tasks: {sum(e['tasks'] for e in employee_data)}
• Total QAs: {sum(e['qa'] for e in employee_data)}
• Total Issues: {sum(e['issues'] for e in employee_data)}"""
            
            # Send to TOPIC_DAILY_SYNC
            await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=report_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_DAILY_SYNC
            )
            
            logger.info(f"✅ Sent daily employee report to TOPIC_DAILY_SYNC")
            
        except Exception as e:
            logger.error(f"Error in _send_daily_report: {e}", exc_info=True)
    
    async def _send_weekly_report(self):
        """Send weekly employee performance report to TOPIC_BOARDROOM."""
        try:
            today = date.today()
            week_start = today - timedelta(days=7)
            
            # Get all users
            user_repo = self.bot_context.bot_data.get('user_repository')
            if not user_repo:
                logger.warning("User repository not available for weekly report")
                return
            
            from src.data.adapters.sqlite_adapter import SQLiteAdapter
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if not isinstance(db_adapter, SQLiteAdapter):
                return
            
            users = await db_adapter.get_all_users()
            
            # Collect weekly data
            employee_data = []
            
            for user in users:
                try:
                    username = f"@{user.username}" if user.username else f"User {user.user_id}"
                    
                    # Get attendance for the week
                    from src.data.repositories.attendance_repository import AttendanceRepository
                    attendance_repo = AttendanceRepository(db_adapter)
                    
                    days_present = 0
                    days_late = 0
                    total_hours = 0.0
                    
                    for i in range(7):
                        check_date = week_start + timedelta(days=i)
                        attendance = await attendance_repo.get_attendance(user.user_id, check_date)
                        if attendance:
                            days_present += 1
                            if attendance.is_late:
                                days_late += 1
                            if attendance.total_hours:
                                total_hours += attendance.total_hours
                    
                    # Get tasks completed this week
                    tasks_completed = 0
                    if self.task_service:
                        from src.data.models.task import TaskState
                        all_tasks = await self.task_service.task_repo.get_tasks_by_assignee(user.user_id)
                        for task in all_tasks:
                            if task.updated_at and week_start <= task.updated_at.date() <= today and task.state == TaskState.APPROVED:
                                tasks_completed += 1
                    
                    employee_data.append({
                        'username': username,
                        'days_present': days_present,
                        'days_late': days_late,
                        'total_hours': total_hours,
                        'tasks': tasks_completed
                    })
                
                except Exception as e:
                    logger.error(f"Error collecting weekly data for user {user.user_id}: {e}")
            
            # Build report
            report_msg = f"""📊 **WEEKLY EMPLOYEE REPORT**

**Week:** {week_start.strftime('%b %d')} - {today.strftime('%b %d, %Y')}
**Generated:** {datetime.now().strftime('%I:%M %p')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            
            for emp in employee_data:
                report_msg += f"""**{emp['username']}**
├ Days Present: {emp['days_present']}/7
├ Late Check-ins: {emp['days_late']}
├ Total Hours: {emp['total_hours']:.1f}h
└ Tasks Completed: {emp['tasks']}

"""
            
            report_msg += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Summary:**
• Total Employees: {len(employee_data)}
• Avg Attendance: {sum(e['days_present'] for e in employee_data) / len(employee_data):.1f}/7 days
• Total Late: {sum(e['days_late'] for e in employee_data)}
• Total Hours: {sum(e['total_hours'] for e in employee_data):.1f}h
• Total Tasks: {sum(e['tasks'] for e in employee_data)}"""
            
            # Send to TOPIC_BOARDROOM
            await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=report_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_BOARDROOM
            )
            
            logger.info(f"✅ Sent weekly employee report to TOPIC_BOARDROOM")
            
        except Exception as e:
            logger.error(f"Error in _send_weekly_report: {e}", exc_info=True)
    
    async def _send_monthly_report(self):
        """Send monthly employee performance report to TOPIC_BOARDROOM."""
        try:
            today = date.today()
            last_month = today.replace(day=1) - timedelta(days=1)
            month_start = last_month.replace(day=1)
            month_name = last_month.strftime('%B %Y')
            
            # Get all users
            user_repo = self.bot_context.bot_data.get('user_repository')
            if not user_repo:
                logger.warning("User repository not available for monthly report")
                return
            
            from src.data.adapters.sqlite_adapter import SQLiteAdapter
            db_adapter = self.bot_context.bot_data.get('db_adapter')
            if not isinstance(db_adapter, SQLiteAdapter):
                return
            
            users = await db_adapter.get_all_users()
            
            # Collect monthly data
            employee_data = []
            
            for user in users:
                try:
                    username = f"@{user.username}" if user.username else f"User {user.user_id}"
                    
                    # Get attendance for the month
                    from src.data.repositories.attendance_repository import AttendanceRepository
                    attendance_repo = AttendanceRepository(db_adapter)
                    
                    days_present = 0
                    days_late = 0
                    total_hours = 0.0
                    
                    # Calculate days in last month
                    days_in_month = (last_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                    total_days = days_in_month.day
                    
                    for i in range(total_days):
                        check_date = month_start + timedelta(days=i)
                        attendance = await attendance_repo.get_attendance(user.user_id, check_date)
                        if attendance:
                            days_present += 1
                            if attendance.is_late:
                                days_late += 1
                            if attendance.total_hours:
                                total_hours += attendance.total_hours
                    
                    # Get tasks completed this month
                    tasks_completed = 0
                    if self.task_service:
                        from src.data.models.task import TaskState
                        all_tasks = await self.task_service.task_repo.get_tasks_by_assignee(user.user_id)
                        for task in all_tasks:
                            if task.updated_at and month_start <= task.updated_at.date() <= last_month and task.state == TaskState.APPROVED:
                                tasks_completed += 1
                    
                    employee_data.append({
                        'username': username,
                        'days_present': days_present,
                        'total_days': total_days,
                        'days_late': days_late,
                        'total_hours': total_hours,
                        'tasks': tasks_completed
                    })
                
                except Exception as e:
                    logger.error(f"Error collecting monthly data for user {user.user_id}: {e}")
            
            # Build report
            report_msg = f"""📊 **MONTHLY EMPLOYEE REPORT**

**Month:** {month_name}
**Generated:** {datetime.now().strftime('%I:%M %p')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            
            for emp in employee_data:
                attendance_rate = (emp['days_present'] / emp['total_days'] * 100) if emp['total_days'] > 0 else 0
                report_msg += f"""**{emp['username']}**
├ Attendance: {emp['days_present']}/{emp['total_days']} days ({attendance_rate:.0f}%)
├ Late Check-ins: {emp['days_late']}
├ Total Hours: {emp['total_hours']:.1f}h
└ Tasks Completed: {emp['tasks']}

"""
            
            report_msg += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Summary:**
• Total Employees: {len(employee_data)}
• Avg Attendance: {sum(e['days_present'] for e in employee_data) / len(employee_data):.1f} days
• Total Late: {sum(e['days_late'] for e in employee_data)}
• Total Hours: {sum(e['total_hours'] for e in employee_data):.1f}h
• Total Tasks: {sum(e['tasks'] for e in employee_data)}"""
            
            # Send to TOPIC_BOARDROOM
            await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=report_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_BOARDROOM
            )
            
            logger.info(f"✅ Sent monthly employee report to TOPIC_BOARDROOM")
            
        except Exception as e:
            logger.error(f"Error in _send_monthly_report: {e}", exc_info=True)
    
    async def _performance_report_loop(self):
        """Background loop for sending performance reports."""
        logger.info("Started performance report loop")
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # Map day names to weekday numbers
                day_map = {
                    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                    "Friday": 4, "Saturday": 5, "Sunday": 6
                }
                
                target_weekday = day_map.get(self.performance_report_day, 0)  # Default to Monday
                
                # Check if it's the configured day and time
                if (now.weekday() == target_weekday and
                    current_time.hour == self.performance_report_time.hour and 
                    current_time.minute == self.performance_report_time.minute):
                    await self._send_performance_report()
                
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance report loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Performance report loop stopped")
    
    async def _send_performance_report(self):
        """Send system performance report to TOPIC_OFFICIAL_DIRECTIVES."""
        try:
            today = date.today()
            week_start = today - timedelta(days=7)
            
            # Collect system metrics
            total_tasks = 0
            completed_tasks = 0
            pending_qas = 0
            open_issues = 0
            
            if self.task_service:
                from src.data.models.task import TaskState
                all_states = [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.APPROVED, TaskState.REJECTED]
                for state in all_states:
                    tasks = await self.task_service.task_repo.get_tasks_by_state(state)
                    total_tasks += len(tasks)
                    if state == TaskState.APPROVED:
                        # Count only this week's completions
                        for task in tasks:
                            if task.updated_at and task.updated_at.date() >= week_start:
                                completed_tasks += 1
            
            if self.qa_service:
                pending_submissions = await self.qa_service.get_pending_submissions()
                pending_qas = len(pending_submissions)
            
            if self.issue_service:
                issues = await self.issue_service.get_open_issues()
                open_issues = len(issues)
            
            # Calculate performance metrics
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Build performance report
            report_msg = f"""📈 **SYSTEM PERFORMANCE REPORT**

**Period:** {week_start.strftime('%b %d')} - {today.strftime('%b %d, %Y')}
**Generated:** {datetime.now().strftime('%A, %I:%M %p')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📊 Task Metrics:**
• Total Active Tasks: {total_tasks}
• Completed This Week: {completed_tasks}
• Completion Rate: {completion_rate:.1f}%

**🔍 QA Metrics:**
• Pending QA Reviews: {pending_qas}

**⚠️ Issue Metrics:**
• Open Issues: {open_issues}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📋 Directives:**

1. **Task Management**
   • Monitor stuck tasks (>72h)
   • Ensure timely QA submissions
   • Address rejected tasks promptly

2. **Quality Assurance**
   • Review pending QAs within 24h
   • Provide detailed feedback on rejections
   • Maintain quality standards

3. **Issue Resolution**
   • Claim and resolve issues within 2h
   • Escalate critical issues immediately
   • Document resolutions properly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Status:** {"🟢 Healthy" if completion_rate > 80 and pending_qas < 5 and open_issues < 10 else "🟡 Needs Attention" if completion_rate > 60 else "🔴 Critical"}"""
            
            # Send to TOPIC_OFFICIAL_DIRECTIVES
            await self.bot_context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=report_msg,
                parse_mode='Markdown',
                message_thread_id=self.config.TOPIC_OFFICIAL_DIRECTIVES
            )
            
            logger.info(f"✅ Sent performance report to TOPIC_OFFICIAL_DIRECTIVES")
            
        except Exception as e:
            logger.error(f"Error in _send_performance_report: {e}", exc_info=True)
    
    def get_status(self) -> dict:
        """Get service status."""
        return {
            "running": self.running,
            "daily_report_time": self.daily_report_time.strftime('%H:%M'),
            "weekly_report_time": self.weekly_report_time.strftime('%H:%M'),
            "weekly_report_day": self.weekly_report_day,
            "monthly_report_time": self.monthly_report_time.strftime('%H:%M'),
            "performance_report_time": self.performance_report_time.strftime('%H:%M'),
            "performance_report_day": self.performance_report_day,
            "check_interval": self.check_interval,
            "daily_report_task_running": self.daily_report_task and not self.daily_report_task.done(),
            "weekly_report_task_running": self.weekly_report_task and not self.weekly_report_task.done(),
            "monthly_report_task_running": self.monthly_report_task and not self.monthly_report_task.done(),
            "performance_report_task_running": self.performance_report_task and not self.performance_report_task.done()
        }
