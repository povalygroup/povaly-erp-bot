"""Violation data model."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class ViolationType(str, Enum):
    """Violation type enumeration."""
    
    FORMAT = "FORMAT"
    WORKFLOW = "WORKFLOW"
    PERMISSION = "PERMISSION"
    ATTENDANCE = "ATTENDANCE"
    PERFORMANCE = "PERFORMANCE"


@dataclass
class Violation:
    """Violation data model."""
    
    id: Optional[int]  # Auto-increment primary key
    user_id: int
    violation_type: ViolationType
    description: str
    context: Dict[str, Any]  # JSON field
    detected_at: datetime
    action_taken: str  # "AUTO_DELETE", "WARNING_SENT", "ESCALATED", "LOGGED"
    message_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert violation to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "violation_type": self.violation_type.value,
            "description": self.description,
            "context": self.context,
            "detected_at": self.detected_at.isoformat(),
            "action_taken": self.action_taken,
            "message_id": self.message_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Violation":
        """Create violation from dictionary."""
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            violation_type=ViolationType(data["violation_type"]),
            description=data["description"],
            context=data["context"],
            detected_at=datetime.fromisoformat(data["detected_at"]),
            action_taken=data["action_taken"],
            message_id=data.get("message_id"),
        )
