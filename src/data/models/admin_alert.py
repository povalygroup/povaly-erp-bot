"""Admin alert model for tracking Admin Control Panel messages."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AdminAlert:
    """Model for admin control panel alerts."""
    
    id: Optional[int]
    message_id: int
    topic_id: int
    alert_type: str  # e.g., "task_escalation", "qa_escalation", "issue_escalation", etc.
    alert_content: str
    created_at: datetime
    acknowledged: bool = False  # 👍 reaction
    resolved: bool = False  # ❤️ reaction
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None  # user_id
    resolved_by: Optional[int] = None  # user_id
