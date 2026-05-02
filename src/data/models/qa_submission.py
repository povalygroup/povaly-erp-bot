"""QA submission data model."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class QAStatus(str, Enum):
    """QA submission status enumeration."""
    
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class QASubmission:
    """QA submission data model."""
    
    id: Optional[int]  # Auto-increment primary key
    ticket: str
    brand: str
    asset: str
    submitter_id: int
    submitted_at: datetime
    message_id: int
    status: QAStatus = QAStatus.PENDING
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert QA submission to dictionary."""
        return {
            "id": self.id,
            "ticket": self.ticket,
            "brand": self.brand,
            "asset": self.asset,
            "submitter_id": self.submitter_id,
            "submitted_at": self.submitted_at.isoformat(),
            "message_id": self.message_id,
            "status": self.status.value,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QASubmission":
        """Create QA submission from dictionary."""
        return cls(
            id=data.get("id"),
            ticket=data["ticket"],
            brand=data["brand"],
            asset=data["asset"],
            submitter_id=data["submitter_id"],
            submitted_at=datetime.fromisoformat(data["submitted_at"]),
            message_id=data["message_id"],
            status=QAStatus(data.get("status", "PENDING")),
            reviewed_by=data.get("reviewed_by"),
            reviewed_at=datetime.fromisoformat(data["reviewed_at"]) if data.get("reviewed_at") else None,
        )
