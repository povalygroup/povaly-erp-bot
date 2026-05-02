"""Main entry point for the Telegram Operations Automation System."""

import asyncio
import logging
import sys
from pathlib import Path

from telegram.ext import Application

from src.config import get_config
from src.bot.application import setup_bot_application
from src.utils.logger import setup_logging


logger = logging.getLogger(__name__)


async def main() -> None:
    """Main application entry point."""
    try:
        # Setup logging
        setup_logging()
        logger.info("Starting Telegram Operations Automation System...")
        
        # Load configuration
        logger.info("Loading configuration...")
        config = get_config()
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Database type: {config.DATABASE_TYPE}")
        logger.info(f"Timezone: {config.TIMEZONE}")
        logger.info(f"Administrators: {len(config.ADMINISTRATORS)}")
        logger.info(f"Managers: {len(config.MANAGERS)}")
        logger.info(f"QA Reviewers: {len(config.QA_REVIEWERS)}")
        logger.info(f"Owners: {len(config.OWNERS)}")
        
        # Create data directory if it doesn't exist
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        (data_dir / "logs").mkdir(exist_ok=True)
        (data_dir / "backups").mkdir(exist_ok=True)
        logger.info(f"Data directory initialized: {data_dir.absolute()}")
        
        # Setup bot application
        logger.info("Setting up bot application...")
        application = await setup_bot_application(config)
        logger.info("Bot application setup complete")
        
        # Start the bot
        logger.info("Starting bot...")
        logger.info(f"Bot is now running. Press Ctrl+C to stop.")
        
        # Run the bot until Ctrl+C is pressed
        await application.initialize()
        await application.start()
        
        # Start escalation service
        escalation_service = application.bot_data.get("escalation_service")
        if escalation_service:
            await escalation_service.start()
            logger.info("Escalation service started")
        
        # Start QA escalation service
        qa_escalation_service = application.bot_data.get("qa_escalation_service")
        if qa_escalation_service:
            await qa_escalation_service.start()
            logger.info("QA escalation service started")
        
        # Start archive service
        archive_service = application.bot_data.get("archive_service")
        if archive_service:
            await archive_service.start()
            logger.info("Archive service started")
        
        # Start attendance service
        attendance_service = application.bot_data.get("attendance_service")
        if attendance_service:
            await attendance_service.start()
            logger.info("Attendance service started")
        
        # Database sync service - COMPLETELY DISABLED
        # The sync service was causing tasks to be deleted incorrectly
        # Keeping it disabled until it can be properly redesigned
        db_sync_service = application.bot_data.get("db_sync_service")
        if db_sync_service:
            # Initialize reality tracking from current database state
            await db_sync_service.initialize_reality_from_database()
            logger.info("Database sync service: Reality tracking initialized")
            
            # DO NOT START - completely disabled
            # await db_sync_service.start()
            logger.info("⚠️ Database sync service DISABLED (not started)")
        
        # Start daily summary service
        daily_summary_service = application.bot_data.get("daily_summary_service")
        if daily_summary_service:
            await daily_summary_service.start()
            logger.info("Daily summary service started")
        
        # Start report service
        report_service = application.bot_data.get("report_service")
        if report_service:
            await report_service.start()
            logger.info("Report service started")
        
        await application.updater.start_polling(
            allowed_updates=["message", "message_reaction", "callback_query"]
        )
        
        # Keep the bot running
        stop_event = asyncio.Event()
        
        def signal_handler():
            logger.info("Received stop signal, shutting down...")
            stop_event.set()
        
        # Register signal handlers
        try:
            import signal
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, signal_handler)
        except (ImportError, NotImplementedError):
            # Windows doesn't support add_signal_handler
            pass
        
        # Wait for stop signal
        await stop_event.wait()
        
        # Shutdown
        logger.info("Shutting down bot...")
        
        # Stop escalation service
        escalation_service = application.bot_data.get("escalation_service")
        if escalation_service:
            await escalation_service.stop()
            logger.info("Escalation service stopped")
        
        # Stop QA escalation service
        qa_escalation_service = application.bot_data.get("qa_escalation_service")
        if qa_escalation_service:
            await qa_escalation_service.stop()
            logger.info("QA escalation service stopped")
        
        # Stop archive service
        archive_service = application.bot_data.get("archive_service")
        if archive_service:
            await archive_service.stop()
            logger.info("Archive service stopped")
        
        # Stop attendance service
        attendance_service = application.bot_data.get("attendance_service")
        if attendance_service:
            await attendance_service.stop()
            logger.info("Attendance service stopped")
        
        # Stop database sync service
        db_sync_service = application.bot_data.get("db_sync_service")
        if db_sync_service:
            await db_sync_service.stop()
            logger.info("Database sync service stopped")
        
        # Stop daily summary service
        daily_summary_service = application.bot_data.get("daily_summary_service")
        if daily_summary_service:
            await daily_summary_service.stop()
            logger.info("Daily summary service stopped")
        
        # Stop report service
        report_service = application.bot_data.get("report_service")
        if report_service:
            await report_service.stop()
            logger.info("Report service stopped")
        
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        logger.info("Bot shutdown complete")
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


def run():
    """Run the application."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.exception(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
