"""Repository for admin alert operations."""

import logging
from datetime import datetime, date
from typing import List, Optional

from src.data.models.admin_alert import AdminAlert

logger = logging.getLogger(__name__)


class AdminAlertRepository:
    """Repository for managing admin alerts."""
    
    def __init__(self, db_adapter):
        """Initialize repository."""
        self.db = db_adapter
    
    async def create_alert(self, alert: AdminAlert) -> bool:
        """Create a new admin alert."""
        try:
            query = """
                INSERT INTO admin_alerts (
                    message_id, topic_id, alert_type, alert_content,
                    created_at, acknowledged, resolved
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute(
                query,
                (
                    alert.message_id,
                    alert.topic_id,
                    alert.alert_type,
                    alert.alert_content,
                    alert.created_at,
                    alert.acknowledged,
                    alert.resolved
                )
            )
            
            logger.info(f"Created admin alert for message {alert.message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating admin alert: {e}")
            return False
    
    async def get_alert_by_message_id(self, message_id: int) -> Optional[AdminAlert]:
        """Get alert by message ID."""
        try:
            query = """
                SELECT id, message_id, topic_id, alert_type, alert_content,
                       created_at, acknowledged, resolved, acknowledged_at,
                       resolved_at, acknowledged_by, resolved_by
                FROM admin_alerts
                WHERE message_id = ?
            """
            
            result = await self.db.fetch_one(query, (message_id,))
            
            if result:
                return AdminAlert(
                    id=result[0],
                    message_id=result[1],
                    topic_id=result[2],
                    alert_type=result[3],
                    alert_content=result[4],
                    created_at=result[5],
                    acknowledged=bool(result[6]),
                    resolved=bool(result[7]),
                    acknowledged_at=result[8],
                    resolved_at=result[9],
                    acknowledged_by=result[10],
                    resolved_by=result[11]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting alert by message ID: {e}")
            return None
    
    async def mark_acknowledged(self, message_id: int, user_id: int) -> bool:
        """Mark alert as acknowledged (👍 reaction)."""
        try:
            query = """
                UPDATE admin_alerts
                SET acknowledged = 1,
                    acknowledged_at = ?,
                    acknowledged_by = ?
                WHERE message_id = ?
            """
            
            await self.db.execute(query, (datetime.now(), user_id, message_id))
            logger.info(f"Marked alert {message_id} as acknowledged by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking alert as acknowledged: {e}")
            return False
    
    async def mark_resolved(self, message_id: int, user_id: int) -> bool:
        """Mark alert as resolved (❤️ reaction)."""
        try:
            query = """
                UPDATE admin_alerts
                SET resolved = 1,
                    resolved_at = ?,
                    resolved_by = ?
                WHERE message_id = ?
            """
            
            await self.db.execute(query, (datetime.now(), user_id, message_id))
            logger.info(f"Marked alert {message_id} as resolved by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking alert as resolved: {e}")
            return False
    
    async def unmark_acknowledged(self, message_id: int) -> bool:
        """Unmark alert as acknowledged (remove 👍 reaction)."""
        try:
            query = """
                UPDATE admin_alerts
                SET acknowledged = 0,
                    acknowledged_at = NULL,
                    acknowledged_by = NULL
                WHERE message_id = ?
            """
            
            await self.db.execute(query, (message_id,))
            logger.info(f"Unmarked alert {message_id} as acknowledged")
            return True
            
        except Exception as e:
            logger.error(f"Error unmarking alert as acknowledged: {e}")
            return False
    
    async def unmark_resolved(self, message_id: int) -> bool:
        """Unmark alert as resolved (remove ❤️ reaction)."""
        try:
            query = """
                UPDATE admin_alerts
                SET resolved = 0,
                    resolved_at = NULL,
                    resolved_by = NULL
                WHERE message_id = ?
            """
            
            await self.db.execute(query, (message_id,))
            logger.info(f"Unmarked alert {message_id} as resolved")
            return True
            
        except Exception as e:
            logger.error(f"Error unmarking alert as resolved: {e}")
            return False
    
    async def get_unresolved_alerts(self) -> List[AdminAlert]:
        """Get all unresolved alerts (no ❤️ reaction)."""
        try:
            query = """
                SELECT id, message_id, topic_id, alert_type, alert_content,
                       created_at, acknowledged, resolved, acknowledged_at,
                       resolved_at, acknowledged_by, resolved_by
                FROM admin_alerts
                WHERE resolved = 0
                ORDER BY created_at DESC
            """
            
            results = await self.db.fetch_all(query)
            
            alerts = []
            for row in results:
                alerts.append(AdminAlert(
                    id=row[0],
                    message_id=row[1],
                    topic_id=row[2],
                    alert_type=row[3],
                    alert_content=row[4],
                    created_at=row[5],
                    acknowledged=bool(row[6]),
                    resolved=bool(row[7]),
                    acknowledged_at=row[8],
                    resolved_at=row[9],
                    acknowledged_by=row[10],
                    resolved_by=row[11]
                ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting unresolved alerts: {e}")
            return []
    
    async def get_alerts_by_date(self, target_date: date) -> List[AdminAlert]:
        """Get all alerts created on a specific date."""
        try:
            query = """
                SELECT id, message_id, topic_id, alert_type, alert_content,
                       created_at, acknowledged, resolved, acknowledged_at,
                       resolved_at, acknowledged_by, resolved_by
                FROM admin_alerts
                WHERE DATE(created_at) = ?
                ORDER BY created_at DESC
            """
            
            results = await self.db.fetch_all(query, (target_date,))
            
            alerts = []
            for row in results:
                alerts.append(AdminAlert(
                    id=row[0],
                    message_id=row[1],
                    topic_id=row[2],
                    alert_type=row[3],
                    alert_content=row[4],
                    created_at=row[5],
                    acknowledged=bool(row[6]),
                    resolved=bool(row[7]),
                    acknowledged_at=row[8],
                    resolved_at=row[9],
                    acknowledged_by=row[10],
                    resolved_by=row[11]
                ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting alerts by date: {e}")
            return []
