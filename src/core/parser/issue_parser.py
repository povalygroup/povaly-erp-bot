"""Issue parser for Core Operations system."""

import re
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

from src.data.models.issue import Issue, IssuePriority

logger = logging.getLogger(__name__)


@dataclass
class IssueData:
    """Parsed issue data."""
    ticket: str
    title: str
    details: str
    priority: IssuePriority
    assignee_username: Optional[str] = None
    issue_ticket: Optional[str] = None  # Optional, will be auto-generated if not provided


class IssueParser:
    """Parser for issue messages in Core Operations."""
    
    def __init__(self):
        """Initialize parser."""
        # Issue format patterns
        self.ticket_pattern = re.compile(r'\[TICKET\]\s*#?([A-Z]{3}\d{6})', re.IGNORECASE)
        self.issue_ticket_pattern = re.compile(r'\[ISSUETICKET\]\s*#?([A-Z]{3}\d{6}-I\d+)', re.IGNORECASE)
        self.issue_pattern = re.compile(r'\[ISSUE\]\s*(.+?)(?=\[|$)', re.IGNORECASE | re.DOTALL)
        self.details_pattern = re.compile(r'\[DETAILS\]\s*(.+?)(?=\[|$)', re.IGNORECASE | re.DOTALL)
        self.priority_pattern = re.compile(r'\[PRIORITY\]\s*(LOW|MEDIUM|HIGH|CRITICAL)', re.IGNORECASE)
        self.assignee_pattern = re.compile(r'\[ASSIGNEE\]\s*@?(\w+)', re.IGNORECASE)
        
        # Required fields for validation (ISSUETICKET is optional)
        self.required_fields = ['TICKET', 'ISSUE', 'DETAILS', 'PRIORITY']
    
    def validate_format(self, text: str) -> Tuple[bool, str]:
        """
        Validate if text matches issue format.
        
        Args:
            text: Message text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Empty message"
        
        # Check for required field markers
        missing_fields = []
        for field in self.required_fields:
            pattern = re.compile(rf'\[{field}\]', re.IGNORECASE)
            if not pattern.search(text):
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate ticket format
        ticket_match = self.ticket_pattern.search(text)
        if not ticket_match:
            return False, "Invalid or missing ticket format. Use: [TICKET] #POV260406"
        
        # Validate priority
        priority_match = self.priority_pattern.search(text)
        if not priority_match:
            return False, "Invalid priority. Use: LOW, MEDIUM, HIGH, or CRITICAL"
        
        # Check if issue title is not empty
        issue_match = self.issue_pattern.search(text)
        if not issue_match or not issue_match.group(1).strip():
            return False, "Issue title cannot be empty"
        
        # Check if details are not empty
        details_match = self.details_pattern.search(text)
        if not details_match or not details_match.group(1).strip():
            return False, "Issue details cannot be empty"
        
        return True, ""
    
    def parse_issue(self, text: str) -> Optional[IssueData]:
        """
        Parse issue data from message text.
        
        Args:
            text: Message text to parse
            
        Returns:
            IssueData object or None if parsing fails
        """
        try:
            # Validate format first
            is_valid, error_msg = self.validate_format(text)
            if not is_valid:
                logger.warning(f"Issue format validation failed: {error_msg}")
                return None
            
            # Extract ticket
            ticket_match = self.ticket_pattern.search(text)
            if not ticket_match:
                logger.error("Failed to extract ticket")
                return None
            
            ticket = ticket_match.group(1).upper()
            # Keep ticket format as-is (no dashes)
            # Remove any existing dashes if present
            ticket = ticket.replace('-', '')
            
            # Extract issue title
            issue_match = self.issue_pattern.search(text)
            if not issue_match:
                logger.error("Failed to extract issue title")
                return None
            
            title = issue_match.group(1).strip()
            
            # Extract details
            details_match = self.details_pattern.search(text)
            if not details_match:
                logger.error("Failed to extract issue details")
                return None
            
            details = details_match.group(1).strip()
            
            # Extract priority
            priority_match = self.priority_pattern.search(text)
            if not priority_match:
                logger.error("Failed to extract priority")
                return None
            
            try:
                priority = IssuePriority(priority_match.group(1).upper())
            except ValueError:
                logger.error(f"Invalid priority value: {priority_match.group(1)}")
                return None
            
            # Extract assignee (optional)
            assignee_username = None
            assignee_match = self.assignee_pattern.search(text)
            if assignee_match:
                assignee_username = assignee_match.group(1)
            
            # Extract issue_ticket (optional)
            issue_ticket = None
            issue_ticket_match = self.issue_ticket_pattern.search(text)
            if issue_ticket_match:
                issue_ticket = issue_ticket_match.group(1).upper()
                logger.info(f"User provided issue_ticket: {issue_ticket}")
            
            return IssueData(
                ticket=ticket,
                title=title,
                details=details,
                priority=priority,
                assignee_username=assignee_username,
                issue_ticket=issue_ticket
            )
            
        except Exception as e:
            logger.error(f"Error parsing issue: {e}")
            return None
    
    def is_issue_format(self, text: str) -> bool:
        """
        Quick check if text looks like an issue format.
        
        Args:
            text: Message text to check
            
        Returns:
            True if text appears to be issue format
        """
        if not text:
            return False
        
        # Look for key markers
        has_ticket = bool(re.search(r'\[TICKET\]', text, re.IGNORECASE))
        has_issue = bool(re.search(r'\[ISSUE\]', text, re.IGNORECASE))
        has_priority = bool(re.search(r'\[PRIORITY\]', text, re.IGNORECASE))
        
        # Must have at least ticket and issue markers
        return has_ticket and has_issue
    
    def extract_ticket_from_text(self, text: str) -> Optional[str]:
        """
        Extract just the ticket ID from any text.
        
        Args:
            text: Text that might contain a ticket ID
            
        Returns:
            Ticket ID or None if not found
        """
        # Try different ticket patterns
        patterns = [
            r'#([A-Z]{3}\d{6})',  # #POV260406
            r'([A-Z]{3}\d{6})',   # POV260406
            r'\[TICKET\]\s*#?([A-Z]{3}\d{6})',  # [TICKET] #POV260406
            r'#([A-Z]{3}-\d{4}-\d+)',  # #POV-2604-06 (backward compatibility)
            r'([A-Z]{3}-\d{4}-\d+)',   # POV-2604-06 (backward compatibility)
            r'\[TICKET\]\s*#?([A-Z]{3}-\d{4}-\d+)'  # [TICKET] #POV-2604-06 (backward compatibility)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ticket = match.group(1).upper()
                # Keep format without dashes
                ticket = ticket.replace('-', '')
                return ticket
        
        return None
    
    def format_issue_template(self, ticket: str = "", assignee: str = "", issue_ticket: str = "") -> str:
        """
        Generate issue template.
        
        Args:
            ticket: Pre-filled ticket ID (should be existing task ticket)
            assignee: Pre-filled assignee username
            issue_ticket: Pre-filled issue ticket (e.g., POV260409-I1)
            
        Returns:
            Formatted issue template
        """
        template = f"""[TICKET] #{ticket if ticket else 'POV260406 (existing task ticket)'}
[ISSUETICKET] #{issue_ticket if issue_ticket else 'Auto-generated (e.g., POV260406-I1)'}
[ISSUE] Short descriptive title
[DETAILS] Detailed explanation of the issue, steps to reproduce, expected vs actual behavior
[PRIORITY] LOW / MEDIUM / HIGH / CRITICAL
[ASSIGNEE] @{assignee if assignee else 'username (optional)'}"""
        
        return template