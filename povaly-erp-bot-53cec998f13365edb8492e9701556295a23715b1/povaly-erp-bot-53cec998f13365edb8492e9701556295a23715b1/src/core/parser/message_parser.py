"""Message parser for extracting structured data from Telegram messages."""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaskMessage:
    """Parsed task allocation message."""
    ticket: str
    brand: str
    task_description: str
    assignee_username: str
    deadline: Optional[str] = None
    resources: Optional[str] = None


@dataclass
class QAMessage:
    """Parsed QA submission message."""
    ticket: str
    brand: str
    asset: str


@dataclass
class RejectMessage:
    """Parsed rejection feedback message."""
    ticket: str
    issue_type: str
    problem: str
    fix_required: str
    assignee_username: str


class MessageParser:
    """Parser for Telegram messages with multi-line field format."""
    
    def parse_task_allocation(self, text: str) -> Optional[TaskMessage]:
        """
        Parse task allocation message.
        Format:
        [TICKET] #POV260406  (or leave empty for auto-generation)
        [BRAND] #VorosaBajar
        [TASK] Product page SEO optimization
        [ASSIGNEE] @imran
        [DEADLINE] 28 Apr 2026 | 6:00 PM GMT+6
        [RESOURCES] Google Doc Link
        """
        fields = self._extract_fields(text)
        
        # Required fields - TICKET field must exist but can be empty
        if 'TICKET' not in fields or 'ASSIGNEE' not in fields:
            return None
        
        # Ticket can be empty (for auto-generation) or have a value
        ticket = fields['TICKET'].replace('#', '').strip()
        assignee = fields['ASSIGNEE'].replace('@', '').strip()
        
        # Extract brand from BRAND field or ticket
        if 'BRAND' in fields:
            brand = fields['BRAND'].replace('#', '').strip()
        elif ticket and '-' in ticket:
            # Extract from ticket (first part before dash)
            brand = ticket.split('-')[0]
        else:
            # No brand specified and no ticket - will need brand for auto-generation
            brand = 'POV'  # Default brand
        
        # Task description
        task_desc = fields.get('TASK', 'No description provided')
        
        # Optional fields
        deadline = fields.get('DEADLINE')
        resources = fields.get('RESOURCES')
        
        return TaskMessage(
            ticket=ticket,  # Can be empty string for auto-generation
            brand=brand,
            task_description=task_desc,
            assignee_username=assignee,
            deadline=deadline,
            resources=resources
        )
    
    def parse_qa_submission(self, text: str) -> Optional[QAMessage]:
        """
        Parse QA submission message.
        Format:
        [TICKET] #POV260406
        [BRAND] #GSMAura
        [ASSET] https://gsmaura.com/blog/budget-smartphones-2026
        """
        fields = self._extract_fields(text)
        
        # Required fields
        if 'TICKET' not in fields or 'BRAND' not in fields or 'ASSET' not in fields:
            return None
        
        ticket = fields['TICKET'].replace('#', '').strip()
        brand = fields['BRAND'].replace('#', '').strip()
        asset = fields['ASSET'].strip()
        
        return QAMessage(
            ticket=ticket,
            brand=brand,
            asset=asset
        )
    
    def parse_reject_feedback(self, text: str) -> Optional[RejectMessage]:
        """
        Parse rejection feedback message.
        Format:
        [TICKET] #POV260406
        [ISSUE] Quality Issue
        [PROBLEM] Low resolution
        [FIX] Increase to 1080p
        [ASSIGNEE] @username
        """
        fields = self._extract_fields(text)
        
        # Required fields
        required = ['TICKET', 'ISSUE', 'PROBLEM', 'FIX', 'ASSIGNEE']
        if not all(field in fields for field in required):
            return None
        
        return RejectMessage(
            ticket=fields['TICKET'].replace('#', '').strip(),
            issue_type=fields['ISSUE'].strip(),
            problem=fields['PROBLEM'].strip(),
            fix_required=fields['FIX'].strip(),
            assignee_username=fields['ASSIGNEE'].replace('@', '').strip()
        )
    
    def _extract_fields(self, text: str) -> Dict[str, str]:
        """
        Extract all [FIELD] value pairs from message.
        Works with or without line breaks, handles spacing issues.
        Returns dict like: {'TICKET': '#POV260406', 'BRAND': '#VorosaBajar', ...}
        
        Robust parsing:
        - Handles missing spaces between fields
        - Handles extra spaces
        - Works with inline or multi-line format
        - Treats [] as field delimiters
        """
        fields = {}
        
        # Pattern: [FIELD_NAME] followed by value until next [FIELD_NAME] or end
        # This works whether fields are on same line or different lines
        # (?=\s*\[|$) - lookahead for next [ or end of string
        pattern = r'\[([A-Z_]+)\]\s*([^\[]+?)(?=\s*\[|$)'
        
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            field_name = match.group(1).strip()
            field_value = match.group(2).strip()
            
            # Clean up field value: remove extra whitespace but preserve structure
            # Replace multiple spaces/newlines with single space
            field_value = re.sub(r'\s+', ' ', field_value).strip()
            
            fields[field_name] = field_value
        
        return fields
    
    def extract_ticket(self, text: str) -> Optional[str]:
        """Extract ticket ID from any message."""
        # Look for [TICKET] field first
        fields = self._extract_fields(text)
        if 'TICKET' in fields:
            return fields['TICKET'].replace('#', '').strip()
        
        # Fallback: look for #XXX-XXXX-XX pattern
        match = re.search(r'#([A-Z]+-\d+-\d+)', text)
        if match:
            return match.group(1)
        
        return None
    
    def is_task_allocation(self, text: str) -> bool:
        """Check if message is a task allocation."""
        fields = self._extract_fields(text)
        return 'TICKET' in fields and 'ASSIGNEE' in fields
    
    def is_task_message(self, text: str) -> bool:
        """Check if message is a task message (alias for is_task_allocation)."""
        return self.is_task_allocation(text)
    
    def is_qa_submission(self, text: str) -> bool:
        """Check if message is a QA submission."""
        fields = self._extract_fields(text)
        return 'TICKET' in fields and 'BRAND' in fields and 'ASSET' in fields
    
    def is_reject_feedback(self, text: str) -> bool:
        """Check if message is rejection feedback."""
        fields = self._extract_fields(text)
        required = ['TICKET', 'ISSUE', 'PROBLEM', 'FIX', 'ASSIGNEE']
        return all(field in fields for field in required)
    
    def validate_format(self, text: str, message_type: str) -> tuple[bool, Optional[str]]:
        """
        Validate message format and return (is_valid, error_message).
        
        Args:
            text: Message text
            message_type: 'task', 'qa', or 'reject'
        
        Returns:
            (True, None) if valid
            (False, "error message") if invalid
            
        Validation is lenient - as long as required fields exist with [] brackets,
        the message is considered valid. Spacing and formatting issues are handled.
        """
        fields = self._extract_fields(text)
        
        if message_type == 'task':
            # TICKET field must exist (can be empty for auto-generation)
            if 'TICKET' not in fields:
                return False, "❌ Missing [TICKET] field (leave empty for auto-generation)"
            
            # ASSIGNEE is required
            if 'ASSIGNEE' not in fields:
                return False, "❌ Missing [ASSIGNEE] field"
            
            assignee_value = fields['ASSIGNEE'].strip()
            # Assignee should have @ symbol, but be lenient
            if not assignee_value or (not assignee_value.startswith('@') and len(assignee_value) < 2):
                return False, "❌ [ASSIGNEE] must have a username (e.g., @username or username)"
            
            return True, None
        
        elif message_type == 'qa':
            if 'TICKET' not in fields:
                return False, "❌ Missing [TICKET] field"
            if 'BRAND' not in fields:
                return False, "❌ Missing [BRAND] field"
            if 'ASSET' not in fields:
                return False, "❌ Missing [ASSET] field"
            return True, None
        
        elif message_type == 'reject':
            required = ['TICKET', 'ISSUE', 'PROBLEM', 'FIX', 'ASSIGNEE']
            missing = [f for f in required if f not in fields]
            if missing:
                return False, f"❌ Missing fields: {', '.join([f'[{f}]' for f in missing])}"
            return True, None
        
        return False, "❌ Unknown message type"
