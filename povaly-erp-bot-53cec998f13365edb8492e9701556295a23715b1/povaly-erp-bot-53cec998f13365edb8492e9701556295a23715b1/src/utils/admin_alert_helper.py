"""Helper functions for logging admin alerts."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def log_admin_alert(db_adapter, message_id: int, topic_id: int, alert_type: str, alert_content: str):
    """
    Log an admin alert to the database for tracking.
    
    Args:
        db_adapter: Database adapter
        message_id: Telegram message ID
        topic_id: Topic ID where alert was sent
        alert_type: Type of alert (e.g., "task_escalation", "qa_escalation")
        alert_content: Brief description of the alert
    """
    try:
        from src.data.repositories.admin_alert_repository import AdminAlertRepository
        from src.data.models.admin_alert import AdminAlert
        
        admin_alert_repo = AdminAlertRepository(db_adapter)
        
        alert = AdminAlert(
            id=None,
            message_id=message_id,
            topic_id=topic_id,
            alert_type=alert_type,
            alert_content=alert_content,
            created_at=datetime.now(),
            acknowledged=False,
            resolved=False
        )
        
        await admin_alert_repo.create_alert(alert)
        logger.info(f"Logged admin alert: {alert_type} (message_id={message_id})")
        
    except Exception as e:
        logger.error(f"Failed to log admin alert: {e}")
