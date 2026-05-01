"""Break record data model."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class BreakRecord:
    """Break record data model."""
    
    id: Optional[int]  # Auto-increment primary key
    user_id: int
    date: date
    break_start: datetime
    break_end: Optional[datetime] = None
    reason: str = ""
    duration_minutes: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert break record to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "break_start": self.break_start.isoformat(),
            "break_end": self.break_end.isoformat() if self.break_end else None,
            "reason": self.reason,
            "duration_minutes": self.duration_minutes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BreakRecord":
        """Create break record from dictionary."""
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            date=date.fromisoformat(data["date"]),
            break_start=datetime.fromisoformat(data["break_start"]),
            break_end=datetime.fromisoformat(data["break_end"]) if data.get("break_end") else None,
            reason=data.get("reason", ""),
            duration_minutes=data.get("duration_minutes"),
        )
