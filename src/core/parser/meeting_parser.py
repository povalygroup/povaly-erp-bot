"""Meeting parser for extracting structured data from meeting messages."""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MeetingInviteMessage:
    """Parsed meeting invitation message."""
    title: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM - HH:MM GMT+6
    duration: str  # "X hours" or "X minutes"
    location: str
    organizer: str  # @username
    attendees: str  # Comma-separated @usernames
    agenda: str  # Multi-line agenda
    priority: str  # LOW, MEDIUM, HIGH, URGENT
    meeting_id: Optional[str] = None  # User-provided meeting ID (may be blank or wrong)
    preparation: Optional[str] = None


@dataclass
class MeetingNotesMessage:
    """Parsed meeting notes message (posted after meeting)."""
    meeting_id: str  # Reference to original meeting
    date: str
    time: str
    attendees_present: str  # Who actually attended
    agenda: str  # What was discussed
    decisions: str  # Decisions made
    action_items: str  # Action items with assignees
    next_meeting: Optional[str] = None  # YYYY-MM-DD


class MeetingParser:
    """Parser for meeting invitation and notes messages."""
    
    def parse_meeting_invite(self, text: str) -> Optional[MeetingInviteMessage]:
        """
        Parse meeting invitation message.
        Format:
        [MEETING_ID] MTG260501 (optional, auto-generated if blank/wrong)
        [MEETING_INVITE] Meeting title
        [DATE] YYYY-MM-DD
        [TIME] HH:MM - HH:MM GMT+6
        [DURATION] X hours / X minutes
        [LOCATION] Physical location / Zoom link / Telegram call
        [ORGANIZER] @username
        [ATTENDEES] @user1, @user2, @user3
        [AGENDA]
        • Topic 1
        • Topic 2
        [PREPARATION] What to prepare (optional)
        [PRIORITY] LOW / MEDIUM / HIGH / URGENT
        """
        fields = self._extract_fields(text)
        
        # Required fields (MEETING_ID is optional)
        required = ['MEETING_INVITE', 'DATE', 'TIME', 'DURATION', 'LOCATION', 
                   'ORGANIZER', 'ATTENDEES', 'AGENDA', 'PRIORITY']
        
        if not all(field in fields for field in required):
            return None
        
        # Extract meeting ID if provided (remove # if present)
        meeting_id = None
        if 'MEETING_ID' in fields:
            meeting_id = fields['MEETING_ID'].replace('#', '').strip()
            if not meeting_id:  # Empty string
                meeting_id = None
        
        return MeetingInviteMessage(
            title=fields['MEETING_INVITE'].strip(),
            date=fields['DATE'].strip(),
            time=fields['TIME'].strip(),
            duration=fields['DURATION'].strip(),
            location=fields['LOCATION'].strip(),
            organizer=fields['ORGANIZER'].replace('@', '').strip(),
            attendees=fields['ATTENDEES'].strip(),
            agenda=fields['AGENDA'].strip(),
            priority=fields['PRIORITY'].strip().upper(),
            meeting_id=meeting_id,
            preparation=fields.get('PREPARATION', '').strip() if 'PREPARATION' in fields else None
        )
    
    def parse_meeting_notes(self, text: str) -> Optional[MeetingNotesMessage]:
        """
        Parse meeting notes message (posted after meeting).
        Format:
        [MEETING] Meeting title
        [DATE] YYYY-MM-DD
        [TIME] HH:MM - HH:MM
        [ATTENDEES] @user1, @user2, @user3
        [AGENDA] What was discussed
        [DECISIONS] What was decided
        [ACTION_ITEMS] Who does what by when
        [NEXT_MEETING] YYYY-MM-DD (optional)
        """
        fields = self._extract_fields(text)
        
        # Required fields
        required = ['MEETING', 'DATE', 'TIME', 'ATTENDEES', 'AGENDA', 'DECISIONS', 'ACTION_ITEMS']
        
        if not all(field in fields for field in required):
            return None
        
        # Try to extract meeting ID from title if it exists (e.g., "Q2 Planning [MTG-2605-1]")
        title = fields['MEETING'].strip()
        meeting_id = None
        meeting_id_match = re.search(r'\[([A-Z]+-\d+-\d+)\]', title)
        if meeting_id_match:
            meeting_id = meeting_id_match.group(1)
        
        return MeetingNotesMessage(
            meeting_id=meeting_id or '',
            date=fields['DATE'].strip(),
            time=fields['TIME'].strip(),
            attendees_present=fields['ATTENDEES'].strip(),
            agenda=fields['AGENDA'].strip(),
            decisions=fields['DECISIONS'].strip(),
            action_items=fields['ACTION_ITEMS'].strip(),
            next_meeting=fields.get('NEXT_MEETING', '').strip() if 'NEXT_MEETING' in fields else None
        )
    
    def _extract_fields(self, text: str) -> Dict[str, str]:
        """
        Extract all [FIELD] value pairs from message.
        Works with or without line breaks, handles spacing issues.
        Returns dict like: {'MEETING_INVITE': 'Monthly Review', 'DATE': '2026-05-15', ...}
        
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
            
            # For multi-line fields like AGENDA, preserve line breaks but clean up
            # Only collapse multiple spaces on same line, keep newlines
            lines = field_value.split('\n')
            cleaned_lines = [re.sub(r'\s+', ' ', line).strip() for line in lines]
            field_value = '\n'.join(line for line in cleaned_lines if line)
            
            fields[field_name] = field_value
        
        return fields
    
    def extract_meeting_id(self, text: str) -> Optional[str]:
        """Extract meeting ID from any message."""
        # Look for [MEETING_ID] field first
        fields = self._extract_fields(text)
        if 'MEETING_ID' in fields:
            return fields['MEETING_ID'].replace('#', '').strip()
        
        # Fallback: look for #MTG-XXXX-XX pattern
        match = re.search(r'#?(MTG-\d+-\d+)', text)
        if match:
            return match.group(1)
        
        return None
    
    def is_meeting_invite(self, text: str) -> bool:
        """Check if message is a meeting invitation."""
        fields = self._extract_fields(text)
        return 'MEETING_INVITE' in fields and 'DATE' in fields and 'ATTENDEES' in fields
    
    def is_meeting_notes(self, text: str) -> bool:
        """Check if message is meeting notes."""
        fields = self._extract_fields(text)
        return 'MEETING' in fields and 'DECISIONS' in fields and 'ACTION_ITEMS' in fields
    
    def validate_meeting_invite_format(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Validate meeting invitation format and return (is_valid, error_message).
        
        Returns:
            (True, None) if valid
            (False, "error message") if invalid
        """
        fields = self._extract_fields(text)
        
        # Check required fields
        required = ['MEETING_INVITE', 'DATE', 'TIME', 'DURATION', 'LOCATION', 
                   'ORGANIZER', 'ATTENDEES', 'AGENDA', 'PRIORITY']
        
        missing = [f for f in required if f not in fields]
        if missing:
            return False, f"❌ Missing required fields: {', '.join([f'[{f}]' for f in missing])}"
        
        # Validate date format (YYYY-MM-DD)
        date_value = fields['DATE'].strip()
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_value):
            return False, f"❌ Invalid [DATE] format. Use YYYY-MM-DD (e.g., 2026-05-15)"
        
        # Validate time format (HH:MM - HH:MM)
        time_value = fields['TIME'].strip()
        if not re.match(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}', time_value):
            return False, f"❌ Invalid [TIME] format. Use HH:MM - HH:MM (e.g., 14:00 - 15:30)"
        
        # Validate priority
        priority_value = fields['PRIORITY'].strip().upper()
        if priority_value not in ['LOW', 'MEDIUM', 'HIGH', 'URGENT']:
            return False, f"❌ Invalid [PRIORITY]. Must be: LOW, MEDIUM, HIGH, or URGENT"
        
        # Validate organizer has @ symbol
        organizer_value = fields['ORGANIZER'].strip()
        if not organizer_value.startswith('@') and len(organizer_value) < 2:
            return False, f"❌ [ORGANIZER] must be a username (e.g., @username)"
        
        # Validate attendees
        attendees_value = fields['ATTENDEES'].strip()
        if not attendees_value:
            return False, f"❌ [ATTENDEES] cannot be empty"
        
        return True, None
    
    def validate_meeting_notes_format(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Validate meeting notes format and return (is_valid, error_message).
        
        Returns:
            (True, None) if valid
            (False, "error message") if invalid
        """
        fields = self._extract_fields(text)
        
        # Check required fields
        required = ['MEETING', 'DATE', 'TIME', 'ATTENDEES', 'AGENDA', 'DECISIONS', 'ACTION_ITEMS']
        
        missing = [f for f in required if f not in fields]
        if missing:
            return False, f"❌ Missing required fields: {', '.join([f'[{f}]' for f in missing])}"
        
        # Validate date format
        date_value = fields['DATE'].strip()
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_value):
            return False, f"❌ Invalid [DATE] format. Use YYYY-MM-DD"
        
        # Validate time format
        time_value = fields['TIME'].strip()
        if not re.match(r'^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}', time_value):
            return False, f"❌ Invalid [TIME] format. Use HH:MM - HH:MM"
        
        return True, None
    
    def parse_duration_to_minutes(self, duration_str: str) -> int:
        """
        Parse duration string to minutes.
        Examples: "1.5 hours" -> 90, "30 minutes" -> 30, "2 hours" -> 120
        """
        duration_str = duration_str.lower().strip()
        
        # Try to extract number
        number_match = re.search(r'(\d+\.?\d*)', duration_str)
        if not number_match:
            return 60  # Default to 1 hour
        
        number = float(number_match.group(1))
        
        # Check if it's hours or minutes
        if 'hour' in duration_str:
            return int(number * 60)
        elif 'minute' in duration_str or 'min' in duration_str:
            return int(number)
        else:
            # Default to minutes if no unit specified
            return int(number)
    
    def parse_attendees_list(self, attendees_str: str) -> list[str]:
        """
        Parse comma-separated attendees string to list of usernames.
        Example: "@user1, @user2, @user3" -> ["user1", "user2", "user3"]
        """
        # Split by comma
        attendees = [a.strip() for a in attendees_str.split(',')]
        
        # Remove @ symbol and clean up
        attendees = [a.replace('@', '').strip() for a in attendees if a.strip()]
        
        return attendees
