"""Report data model."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional, Dict, Any


class ReportType(str, Enum):
    """Report type enumeration."""
    
    DAILY_SYNC = "DAILY_SYNC"
    WEEKLY = "WEEKLY"
    DAILY_SUMMARY = "DAILY_SUMMARY"
    QA_DAILY_SUMMARY = "QA_DAILY_SUMMARY"


@dataclass
class Report:
    """Report data model."""
    
    id: Optional[int]  # Auto-increment primary key
    report_type: ReportType
    date: date
    content: str
    message_id: int
    generated_at: datetime
    user_id: Optional[int] = None  # Null for team-wide reports
    metrics: Optional[Dict[str, Any]] = None  # JSON field
    
    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "id": self.id,
            "report_type": self.report_type.value,
            "date": self.date.isoformat(),
            "content": self.content,
            "message_id": self.message_id,
            "generated_at": self.generated_at.isoformat(),
            "user_id": self.user_id,
            "metrics": self.metrics,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Report":
        """Create report from dictionary."""
        return cls(
            id=data.get("id"),
            report_type=ReportType(data["report_type"]),
            date=date.fromisoformat(data["date"]),
            content=data["content"],
            message_id=data["message_id"],
            generated_at=datetime.fromisoformat(data["generated_at"]),
            user_id=data.get("user_id"),
            metrics=data.get("metrics"),
        )
