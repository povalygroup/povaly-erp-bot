"""Task data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskState(str, Enum):
    """Task state enumeration."""
    
    ASSIGNED = "ASSIGNED"
    STARTED = "STARTED"
    QA_SUBMITTED = "QA_SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"
    INACTIVE = "INACTIVE"


@dataclass
class Task:
    """Task data model."""
    
    ticket: str  # Primary key (e.g., "PV-2404-1")
    brand: str
    assignee_id: int
    creator_id: int
    state: TaskState
    created_at: datetime
    message_id: int
    topic_id: int
    
    # Optional timestamps
    started_at: Optional[datetime] = None
    qa_submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Fire emoji exemption
    has_fire_exemption: bool = False
    fire_exemption_by: Optional[int] = None
    fire_exemption_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "ticket": self.ticket,
            "brand": self.brand,
            "assignee_id": self.assignee_id,
            "creator_id": self.creator_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "message_id": self.message_id,
            "topic_id": self.topic_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "qa_submitted_at": self.qa_submitted_at.isoformat() if self.qa_submitted_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "has_fire_exemption": self.has_fire_exemption,
            "fire_exemption_by": self.fire_exemption_by,
            "fire_exemption_at": self.fire_exemption_at.isoformat() if self.fire_exemption_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create task from dictionary."""
        return cls(
            ticket=data["ticket"],
            brand=data["brand"],
            assignee_id=data["assignee_id"],
            creator_id=data["creator_id"],
            state=TaskState(data["state"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            message_id=data["message_id"],
            topic_id=data["topic_id"],
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            qa_submitted_at=datetime.fromisoformat(data["qa_submitted_at"]) if data.get("qa_submitted_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            has_fire_exemption=data.get("has_fire_exemption", False),
            fire_exemption_by=data.get("fire_exemption_by"),
            fire_exemption_at=datetime.fromisoformat(data["fire_exemption_at"]) if data.get("fire_exemption_at") else None,
        )


@dataclass
class TaskReaction:
    """Task reaction data model."""
    
    id: Optional[int]  # Auto-increment primary key
    message_id: int
    ticket: str
    user_id: int
    reaction: str  # "👍", "❤️", "👎", "🔥"
    timestamp: datetime
    topic_id: int
    
    def to_dict(self) -> dict:
        """Convert reaction to dictionary."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "ticket": self.ticket,
            "user_id": self.user_id,
            "reaction": self.reaction,
            "timestamp": self.timestamp.isoformat(),
            "topic_id": self.topic_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TaskReaction":
        """Create reaction from dictionary."""
        return cls(
            id=data.get("id"),
            message_id=data["message_id"],
            ticket=data["ticket"],
            user_id=data["user_id"],
            reaction=data["reaction"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            topic_id=data["topic_id"],
        )


@dataclass
class RejectFeedback:
    """Reject feedback data model."""
    
    id: Optional[int]  # Auto-increment primary key
    ticket: str
    issue_type: str
    problem: str
    fix_required: str
    assignee_id: int
    reviewer_id: int
    created_at: datetime
    message_id: int
    
    def to_dict(self) -> dict:
        """Convert feedback to dictionary."""
        return {
            "id": self.id,
            "ticket": self.ticket,
            "issue_type": self.issue_type,
            "problem": self.problem,
            "fix_required": self.fix_required,
            "assignee_id": self.assignee_id,
            "reviewer_id": self.reviewer_id,
            "created_at": self.created_at.isoformat(),
            "message_id": self.message_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RejectFeedback":
        """Create feedback from dictionary."""
        return cls(
            id=data.get("id"),
            ticket=data["ticket"],
            issue_type=data["issue_type"],
            problem=data["problem"],
            fix_required=data["fix_required"],
            assignee_id=data["assignee_id"],
            reviewer_id=data["reviewer_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            message_id=data["message_id"],
        )


@dataclass
class Archive:
    """Archive data model."""
    
    id: Optional[int]  # Auto-increment primary key
    ticket: str
    assignee_id: int
    qa_reviewer_id: int
    archived_at: datetime
    original_message_id: int
    qa_message_id: int
    archive_message_id: int
    completion_time_hours: float
    
    def to_dict(self) -> dict:
        """Convert archive to dictionary."""
        return {
            "id": self.id,
            "ticket": self.ticket,
            "assignee_id": self.assignee_id,
            "qa_reviewer_id": self.qa_reviewer_id,
            "archived_at": self.archived_at.isoformat(),
            "original_message_id": self.original_message_id,
            "qa_message_id": self.qa_message_id,
            "archive_message_id": self.archive_message_id,
            "completion_time_hours": self.completion_time_hours,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Archive":
        """Create archive from dictionary."""
        return cls(
            id=data.get("id"),
            ticket=data["ticket"],
            assignee_id=data["assignee_id"],
            qa_reviewer_id=data["qa_reviewer_id"],
            archived_at=datetime.fromisoformat(data["archived_at"]),
            original_message_id=data["original_message_id"],
            qa_message_id=data["qa_message_id"],
            archive_message_id=data["archive_message_id"],
            completion_time_hours=data["completion_time_hours"],
        )
