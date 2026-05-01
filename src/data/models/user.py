"""User data model."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    """User role enumeration."""
    
    REGULAR = "regular"
    QA_REVIEWER = "qa_reviewer"
    MANAGER = "manager"
    ADMIN = "admin"
    OWNER = "owner"


@dataclass
class User:
    """User data model."""
    
    user_id: int  # Telegram user ID (primary key)
    username: str
    full_name: str
    role: UserRole
    created_at: datetime
    last_active: datetime
    is_on_leave: bool = False
    leave_start: Optional[datetime] = None
    leave_end: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "is_on_leave": self.is_on_leave,
            "leave_start": self.leave_start.isoformat() if self.leave_start else None,
            "leave_end": self.leave_end.isoformat() if self.leave_end else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create user from dictionary."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            full_name=data["full_name"],
            role=UserRole(data["role"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]),
            is_on_leave=data.get("is_on_leave", False),
            leave_start=datetime.fromisoformat(data["leave_start"]) if data.get("leave_start") else None,
            leave_end=datetime.fromisoformat(data["leave_end"]) if data.get("leave_end") else None,
        )
