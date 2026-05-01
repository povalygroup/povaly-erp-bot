"""Attendance data model."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Attendance:
    """Attendance data model."""
    
    id: Optional[int]  # Auto-increment primary key
    user_id: int
    date: date
    checkin_time: datetime
    checkout_time: Optional[datetime] = None
    is_late: bool = False
    is_auto_checkout: bool = False
    total_hours: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert attendance to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "checkin_time": self.checkin_time.isoformat(),
            "checkout_time": self.checkout_time.isoformat() if self.checkout_time else None,
            "is_late": self.is_late,
            "is_auto_checkout": self.is_auto_checkout,
            "total_hours": self.total_hours,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Attendance":
        """Create attendance from dictionary."""
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            date=date.fromisoformat(data["date"]),
            checkin_time=datetime.fromisoformat(data["checkin_time"]),
            checkout_time=datetime.fromisoformat(data["checkout_time"]) if data.get("checkout_time") else None,
            is_late=data.get("is_late", False),
            is_auto_checkout=data.get("is_auto_checkout", False),
            total_hours=data.get("total_hours"),
        )
