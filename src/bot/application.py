"""Bot application setup."""

import logging
from telegram.ext import Application

from src.config import Config
from src.data.adapters.factory import create_database_adapter
from src.data.repositories import TaskRepository, UserRepository, QARepository, IssueRepository
from src.core.state.state_engine import StateEngine
from src.services import TaskService, QAService, IssueService, EscalationService
from src.services.database_sync_service import DatabaseSyncService
from src.services.topic_scanner_service import TopicScannerService
from src.bot.handlers.command_handler import setup_command_handlers, handle_newissue_task_selection, handle_newissue_priority_selection
from src.bot.handlers.message_handler import setup_message_handlers
from src.bot.handlers.reaction_handler import setup_reaction_handlers

logger = logging.getLogger(__name__)


async def setup_bot_application(config: Config) -> Application:
    """
    Setup and configure the bot application.
    
    Args:
        config: System configuration
    
    Returns:
        Configured Application instance
    """
    logger.info("Building bot application...")
    
    # Initialize database
    logger.info("Initializing database...")
    db_adapter = create_database_adapter(config)
    await db_adapter.initialize()
    logger.info("Database initialized successfully")
    
    # Run migrations
    logger.info("Running database migrations...")
    from src.data.migrations import MigrationManager
    migration_manager = MigrationManager(db_adapter)
    await migration_manager.run_all_pending_migrations()
    logger.info("Database migrations completed")
    
    # Create repositories
    task_repo = TaskRepository(db_adapter)
    user_repo = UserRepository(db_adapter)
    qa_repo = QARepository(db_adapter)
    issue_repo = IssueRepository(db_adapter)
    
    # Create meeting repository
    from src.data.repositories.meeting_repository import MeetingRepository
    meeting_repo = MeetingRepository(db_adapter)
    
    # Create state engine
    state_engine = StateEngine(task_repo)
    
    # Create services
    task_service = TaskService(task_repo, user_repo, state_engine, config)
    qa_service = QAService(task_repo, qa_repo, state_engine)
    issue_service = IssueService(db_adapter)
    
    # Create meeting service
    from src.services.meeting_service import MeetingService
    meeting_service = MeetingService(meeting_repo, user_repo, config)
    
    # Create application
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )
    
    # Create bot context object for services
    class BotContext:
        def __init__(self, bot, bot_data):
            self.bot = bot
            self.bot_data = bot_data
    
    bot_context = BotContext(application.bot, application.bot_data)
    
    # Create meeting reminder service
    from src.services.meeting_reminder_service import MeetingReminderService
    meeting_reminder_service = MeetingReminderService(meeting_repo, user_repo, bot_context, config)
    
    # Create escalation service (needs bot context and task service)
    escalation_service = EscalationService(issue_service, application, config, task_service)
    
    # Create QA escalation service
    from src.services.qa_escalation_service import QAEscalationService
    qa_escalation_service = QAEscalationService(qa_service, qa_repo, application, config)
    
    # Create archive service
    from src.services.archive_service import ArchiveService
    archive_service = ArchiveService(task_service, application, config)
    
    # Create attendance service
    from src.services.attendance_service import AttendanceService
    from src.data.repositories.attendance_repository import AttendanceRepository
    attendance_repo = AttendanceRepository(db_adapter)
    attendance_service = AttendanceService(attendance_repo, application, config)
    
    # Create topic scanner service
    topic_scanner = TopicScannerService(config, task_service)
    
    # Create database sync service with topic scanner
    db_sync_service = DatabaseSyncService(task_service, config, topic_scanner)
    
    # Create daily summary service
    from src.services.daily_summary_service import DailySummaryService
    
    # Create bot context object for services
    class BotContext:
        def __init__(self, bot, bot_data):
            self.bot = bot
            self.bot_data = bot_data
    
    daily_summary_service = DailySummaryService(bot_context, config, task_service, issue_service, qa_service)
    
    # Create report service
    from src.services.report_service import ReportService
    report_service = ReportService(bot_context, config, task_service, issue_service, qa_service, attendance_service)
    
    # Create deadline reminder service
    from src.services.deadline_reminder_service import DeadlineReminderService
    deadline_reminder_service = DeadlineReminderService(bot_context, config, task_service)
    
    # Create task routing service
    from src.services.task_routing_service import TaskRoutingService
    task_routing_service = TaskRoutingService(task_service, user_repo, db_adapter, config)
    
    # Create leave request service
    from src.services.leave_request_service import LeaveRequestService
    leave_request_service = LeaveRequestService(attendance_repo, user_repo, task_service, config)
    
    # Create employee info service
    from src.services.employee_info_service import EmployeeInfoService
    employee_info_service = EmployeeInfoService(user_repo, config)
    
    # Create birthday service
    from src.services.birthday_service import BirthdayService
    birthday_service = BirthdayService(user_repo, config)
    
    # DISABLED: Auto-recovery on startup
    # This was deleting tasks from previous runs because the Bot API can't read old messages
    # await topic_scanner.sync_database_with_topic_reality(application)
    logger.info("⚠️ Auto-recovery disabled - database will not be synced with topic on startup")
    
    # STARTUP TASK SYNC: Scan recent messages to register tasks in memory
    logger.info("🔄 Scanning recent task messages for reaction handling...")
    try:
        # Scan last 100 messages in Task Allocation topic
        task_count = await topic_scanner.scan_recent_tasks_for_reactions(application, limit=100)
        logger.info(f"✅ Recent task scan completed - {task_count} tasks ready")
        logger.info("⚠️  NOTE: Reactions on messages created BEFORE bot startup may not trigger events")
        logger.info("💡 TIP: Keep bot running continuously for best reaction handling")
    except Exception as e:
        logger.warning(f"⚠️ Could not scan recent tasks: {e}")
    
    # Store services in bot_data for access in handlers
    application.bot_data["config"] = config
    application.bot_data["task_service"] = task_service
    application.bot_data["qa_service"] = qa_service
    application.bot_data["issue_service"] = issue_service
    application.bot_data["meeting_service"] = meeting_service
    application.bot_data["meeting_reminder_service"] = meeting_reminder_service
    application.bot_data["issue_repository"] = issue_service.repository  # Add issue repository for issue_ticket generation
    application.bot_data["escalation_service"] = escalation_service
    application.bot_data["qa_escalation_service"] = qa_escalation_service
    application.bot_data["archive_service"] = archive_service
    application.bot_data["attendance_service"] = attendance_service
    application.bot_data["db_sync_service"] = db_sync_service
    application.bot_data["topic_scanner"] = topic_scanner
    application.bot_data["daily_summary_service"] = daily_summary_service
    application.bot_data["report_service"] = report_service
    application.bot_data["deadline_reminder_service"] = deadline_reminder_service
    application.bot_data["task_routing_service"] = task_routing_service
    application.bot_data["leave_request_service"] = leave_request_service
    application.bot_data["employee_info_service"] = employee_info_service
    application.bot_data["birthday_service"] = birthday_service
    application.bot_data["db_adapter"] = db_adapter
    application.bot_data["user_repository"] = user_repo  # Add user repository for username lookups
    application.bot_data["attendance_repository"] = attendance_repo  # Add attendance repository for leave requests
    
    # Store application reference in db_sync_service for topic scanner sync
    db_sync_service.application = application
    
    # Setup handlers
    setup_command_handlers(application, config)
    setup_message_handlers(application, config)
    setup_reaction_handlers(application, config)
    
    # Register additional issue creation handlers
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(handle_newissue_task_selection, pattern="^newissue_task:"))
    application.add_handler(CallbackQueryHandler(handle_newissue_priority_selection, pattern="^newissue_priority:"))
    
    logger.info("Bot application built successfully")
    return application
