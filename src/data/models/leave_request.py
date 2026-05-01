"""Leave request data model."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class LeaveStatus(str, Enum):
    """Leave request status enumeration."""
    
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class LeaveRequest:
    """Leave request data model."""
    
    id: Optional[int]  # Auto-increment primary key
    user_id: int
    start_date: date
    end_date: date
    reason: str  # Encrypted
    status: LeaveStatus
    requested_at: datetime
    message_id: int
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert leave request to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "reason": self.reason,
            "status": self.status.value,
            "requested_at": self.requested_at.isoformat(),
            "message_id": self.message_id,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "LeaveRequest":
        """Create leave request from dictionary."""
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            start_date=date.fromisoformat(data["start_date"]),
            end_date=date.fromisoformat(data["end_date"]),
            reason=data["reason"],
            status=LeaveStatus(data["status"]),
            requested_at=datetime.fromisoformat(data["requested_at"]),
            message_id=data["message_id"],
            reviewed_by=data.get("reviewed_by"),
            reviewed_at=datetime.fromisoformat(data["reviewed_at"]) if data.get("reviewed_at") else None,
        )
