"""Issue model for Core Operations system."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class IssueStatus(Enum):
    """Issue status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    INVALID = "invalid"
    ESCALATED = "escalated"


class IssuePriority(Enum):
    """Issue priority enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Issue:
    """Issue data model."""
    
    # Core fields
    ticket: str  # Task ticket (e.g., POV260410)
    issue_ticket: str  # Issue ticket (e.g., POV260410-I1)
    title: str
    details: str
    priority: IssuePriority
    assignee_username: Optional[str] = None
    
    # System fields
    creator_id: int = 0
    message_id: int = 0
    topic_id: int = 0
    status: IssueStatus = IssueStatus.OPEN
    
    # Tracking fields
    created_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    
    # Handler tracking
    claimed_by: List[int] = None  # List of user IDs who reacted with 👍
    resolved_by: Optional[int] = None  # User ID who resolved (❤️)
    rejected_by: Optional[int] = None  # User ID who rejected (👎)
    
    # Escalation tracking
    escalation_sent: bool = False
    reminder_sent: bool = False
    
    def __post_init__(self):
        """Initialize default values."""
        if self.claimed_by is None:
            self.claimed_by = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def is_claimed(self) -> bool:
        """Check if issue is claimed by someone."""
        return len(self.claimed_by) > 0
    
    @property
    def is_resolved(self) -> bool:
        """Check if issue is resolved."""
        return self.status == IssueStatus.RESOLVED
    
    @property
    def is_overdue(self, hours: int = 2) -> bool:
        """Check if issue is overdue for escalation."""
        if self.is_resolved or self.escalation_sent:
            return False
        
        time_diff = datetime.now() - self.created_at
        return time_diff.total_seconds() > (hours * 3600)
    
    @property
    def primary_handler(self) -> Optional[int]:
        """Get the first user who claimed the issue."""
        return self.claimed_by[0] if self.claimed_by else None
    
    def add_claim(self, user_id: int) -> bool:
        """Add a user claim (👍 reaction)."""
        if user_id not in self.claimed_by:
            self.claimed_by.append(user_id)
            if self.status == IssueStatus.OPEN:
                self.status = IssueStatus.IN_PROGRESS
                self.claimed_at = datetime.now()
            return True
        return False
    
    def remove_claim(self, user_id: int) -> bool:
        """Remove a user claim (remove 👍 reaction)."""
        if user_id in self.claimed_by:
            self.claimed_by.remove(user_id)
            # If no more claims, revert to OPEN
            if not self.claimed_by and self.status == IssueStatus.IN_PROGRESS:
                self.status = IssueStatus.OPEN
                self.claimed_at = None
            return True
        return False
    
    def resolve(self, user_id: int) -> bool:
        """Mark issue as resolved (❤️ reaction)."""
        if not self.is_resolved:
            self.status = IssueStatus.RESOLVED
            self.resolved_by = user_id
            self.resolved_at = datetime.now()
            return True
        return False
    
    def reject(self, user_id: int) -> bool:
        """Mark issue as invalid (👎 reaction)."""
        if self.status != IssueStatus.INVALID:
            self.status = IssueStatus.INVALID
            self.rejected_by = user_id
            return True
        return False
    
    def mark_escalated(self) -> bool:
        """Mark issue as escalated."""
        if not self.escalation_sent:
            self.status = IssueStatus.ESCALATED
            self.escalated_at = datetime.now()
            self.escalation_sent = True
            return True
        return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            'ticket': self.ticket,
            'issue_ticket': self.issue_ticket,
            'title': self.title,
            'details': self.details,
            'priority': self.priority.value,
            'assignee_username': self.assignee_username,
            'creator_id': self.creator_id,
            'message_id': self.message_id,
            'topic_id': self.topic_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'claimed_at': self.claimed_at.isoformat() if self.claimed_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'escalated_at': self.escalated_at.isoformat() if self.escalated_at else None,
            'claimed_by': self.claimed_by,
            'resolved_by': self.resolved_by,
            'rejected_by': self.rejected_by,
            'escalation_sent': self.escalation_sent,
            'reminder_sent': self.reminder_sent
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Issue':
        """Create Issue from dictionary."""
        # Parse datetime fields
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        claimed_at = datetime.fromisoformat(data['claimed_at']) if data.get('claimed_at') else None
        resolved_at = datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None
        escalated_at = datetime.fromisoformat(data['escalated_at']) if data.get('escalated_at') else None
        
        return cls(
            ticket=data['ticket'],
            issue_ticket=data.get('issue_ticket', data['ticket']),  # Fallback to ticket for backward compatibility
            title=data['title'],
            details=data['details'],
            priority=IssuePriority(data['priority']),
            assignee_username=data.get('assignee_username'),
            creator_id=data.get('creator_id', 0),
            message_id=data.get('message_id', 0),
            topic_id=data.get('topic_id', 0),
            status=IssueStatus(data.get('status', 'open')),
            created_at=created_at,
            claimed_at=claimed_at,
            resolved_at=resolved_at,
            escalated_at=escalated_at,
            claimed_by=data.get('claimed_by', []),
            resolved_by=data.get('resolved_by'),
            rejected_by=data.get('rejected_by'),
            escalation_sent=data.get('escalation_sent', False),
            reminder_sent=data.get('reminder_sent', False)
        )