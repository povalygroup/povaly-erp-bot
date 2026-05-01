"""Audit trail data model."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class EventType(str, Enum):
    """Event type enumeration."""
    
    STATE_TRANSITION = "STATE_TRANSITION"
    REACTION = "REACTION"
    QA_SUBMISSION = "QA_SUBMISSION"
    VIOLATION = "VIOLATION"
    PERMISSION_CHECK = "PERMISSION_CHECK"
    NOTIFICATION = "NOTIFICATION"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    DATABASE_ERROR = "DATABASE_ERROR"
    TASK_CREATED = "TASK_CREATED"
    LEAVE_REQUEST = "LEAVE_REQUEST"
    ATTENDANCE = "ATTENDANCE"


@dataclass
class AuditTrail:
    """Audit trail data model."""
    
    id: Optional[int]  # Auto-increment primary key
    event_type: EventType
    timestamp: datetime
    context: Dict[str, Any]  # JSON field with full event context
    user_id: Optional[int] = None
    ticket: Optional[str] = None
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    message_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert audit trail to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "user_id": self.user_id,
            "ticket": self.ticket,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "message_id": self.message_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AuditTrail":
        """Create audit trail from dictionary."""
        return cls(
            id=data.get("id"),
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=data["context"],
            user_id=data.get("user_id"),
            ticket=data.get("ticket"),
            before_state=data.get("before_state"),
            after_state=data.get("after_state"),
            message_id=data.get("message_id"),
        )
