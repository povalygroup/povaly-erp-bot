"""Meeting data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class MeetingStatus(str, Enum):
    """Meeting status enumeration."""
    
    SCHEDULED = "SCHEDULED"  # Meeting is scheduled
    REMINDED = "REMINDED"    # Reminders sent
    IN_PROGRESS = "IN_PROGRESS"  # Meeting is happening now
    COMPLETED = "COMPLETED"  # Meeting finished, notes posted
    CANCELLED = "CANCELLED"  # Meeting cancelled
    RESCHEDULED = "RESCHEDULED"  # Meeting rescheduled


class MeetingPriority(str, Enum):
    """Meeting priority enumeration."""
    
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class AttendanceStatus(str, Enum):
    """Attendance status enumeration."""
    
    INVITED = "INVITED"  # Invited but not responded
    ATTENDING = "ATTENDING"  # Confirmed attendance (👍)
    ATTENDING_PREPARED = "ATTENDING_PREPARED"  # Confirmed + prepared (❤️)
    CANNOT_ATTEND = "CANNOT_ATTEND"  # Cannot attend (👎)
    URGENT_CONFLICT = "URGENT_CONFLICT"  # Urgent conflict (🔥)


@dataclass
class Meeting:
    """Meeting data model."""
    
    meeting_id: str  # Primary key (e.g., "MTG-2605-1")
    title: str
    date: datetime  # Meeting date and time
    duration_minutes: int
    location: str  # Physical location, Zoom link, or "Telegram Call"
    organizer_id: int
    agenda: str  # Multi-line agenda items
    priority: MeetingPriority
    status: MeetingStatus
    created_at: datetime
    message_id: int
    topic_id: int
    
    # Optional fields
    preparation: Optional[str] = None  # What attendees should prepare
    notes_message_id: Optional[int] = None  # Link to meeting notes after completion
    cancelled_reason: Optional[str] = None
    rescheduled_to: Optional[str] = None  # New meeting_id if rescheduled
    
    # Timestamps
    reminded_24h_at: Optional[datetime] = None
    reminded_1h_at: Optional[datetime] = None
    reminded_15m_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert meeting to dictionary."""
        return {
            "meeting_id": self.meeting_id,
            "title": self.title,
            "date": self.date.isoformat(),
            "duration_minutes": self.duration_minutes,
            "location": self.location,
            "organizer_id": self.organizer_id,
            "agenda": self.agenda,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "message_id": self.message_id,
            "topic_id": self.topic_id,
            "preparation": self.preparation,
            "notes_message_id": self.notes_message_id,
            "cancelled_reason": self.cancelled_reason,
            "rescheduled_to": self.rescheduled_to,
            "reminded_24h_at": self.reminded_24h_at.isoformat() if self.reminded_24h_at else None,
            "reminded_1h_at": self.reminded_1h_at.isoformat() if self.reminded_1h_at else None,
            "reminded_15m_at": self.reminded_15m_at.isoformat() if self.reminded_15m_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Meeting":
        """Create meeting from dictionary."""
        return cls(
            meeting_id=data["meeting_id"],
            title=data["title"],
            date=datetime.fromisoformat(data["date"]),
            duration_minutes=data["duration_minutes"],
            location=data["location"],
            organizer_id=data["organizer_id"],
            agenda=data["agenda"],
            priority=MeetingPriority(data["priority"]),
            status=MeetingStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            message_id=data["message_id"],
            topic_id=data["topic_id"],
            preparation=data.get("preparation"),
            notes_message_id=data.get("notes_message_id"),
            cancelled_reason=data.get("cancelled_reason"),
            rescheduled_to=data.get("rescheduled_to"),
            reminded_24h_at=datetime.fromisoformat(data["reminded_24h_at"]) if data.get("reminded_24h_at") else None,
            reminded_1h_at=datetime.fromisoformat(data["reminded_1h_at"]) if data.get("reminded_1h_at") else None,
            reminded_15m_at=datetime.fromisoformat(data["reminded_15m_at"]) if data.get("reminded_15m_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            cancelled_at=datetime.fromisoformat(data["cancelled_at"]) if data.get("cancelled_at") else None,
        )


@dataclass
class MeetingAttendee:
    """Meeting attendee data model."""
    
    id: Optional[int]  # Auto-increment primary key
    meeting_id: str
    user_id: int
    status: AttendanceStatus
    invited_at: datetime
    responded_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert attendee to dictionary."""
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "invited_at": self.invited_at.isoformat(),
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MeetingAttendee":
        """Create attendee from dictionary."""
        return cls(
            id=data.get("id"),
            meeting_id=data["meeting_id"],
            user_id=data["user_id"],
            status=AttendanceStatus(data["status"]),
            invited_at=datetime.fromisoformat(data["invited_at"]),
            responded_at=datetime.fromisoformat(data["responded_at"]) if data.get("responded_at") else None,
        )


@dataclass
class MeetingNotes:
    """Meeting notes data model (posted after meeting)."""
    
    id: Optional[int]  # Auto-increment primary key
    meeting_id: str
    posted_by: int
    posted_at: datetime
    message_id: int
    
    # Meeting notes fields
    attendees_present: str  # Comma-separated usernames who attended
    decisions: str  # Decisions made
    action_items: str  # Action items assigned
    next_meeting_date: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert notes to dictionary."""
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "posted_by": self.posted_by,
            "posted_at": self.posted_at.isoformat(),
            "message_id": self.message_id,
            "attendees_present": self.attendees_present,
            "decisions": self.decisions,
            "action_items": self.action_items,
            "next_meeting_date": self.next_meeting_date.isoformat() if self.next_meeting_date else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MeetingNotes":
        """Create notes from dictionary."""
        return cls(
            id=data.get("id"),
            meeting_id=data["meeting_id"],
            posted_by=data["posted_by"],
            posted_at=datetime.fromisoformat(data["posted_at"]),
            message_id=data["message_id"],
            attendees_present=data["attendees_present"],
            decisions=data["decisions"],
            action_items=data["action_items"],
            next_meeting_date=datetime.fromisoformat(data["next_meeting_date"]) if data.get("next_meeting_date") else None,
        )


@dataclass
class MeetingReaction:
    """Meeting RSVP reaction data model."""
    
    id: Optional[int]  # Auto-increment primary key
    meeting_id: str
    message_id: int
    user_id: int
    reaction: str  # "👍", "❤️", "👎", "🔥"
    timestamp: datetime
    
    def to_dict(self) -> dict:
        """Convert reaction to dictionary."""
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "message_id": self.message_id,
            "user_id": self.user_id,
            "reaction": self.reaction,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MeetingReaction":
        """Create reaction from dictionary."""
        return cls(
            id=data.get("id"),
            meeting_id=data["meeting_id"],
            message_id=data["message_id"],
            user_id=data["user_id"],
            reaction=data["reaction"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
