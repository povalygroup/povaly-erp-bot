"""Message format violation detector."""

import re
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class ViolationType(Enum):
    """Types of format violations."""
    MISSING_BRACKETS = "missing_brackets"
    MISSING_MENTION = "missing_mention"
    INVALID_TICKET_FORMAT = "invalid_ticket_format"
    INVALID_BRAND_CODE = "invalid_brand_code"
    DUPLICATE_TICKET = "duplicate_ticket"
    UNAUTHORIZED_USER = "unauthorized_user"
    MISSING_DESCRIPTION = "missing_description"
    MALFORMED_QA_SUBMISSION = "malformed_qa_submission"


@dataclass
class Violation:
    """Represents a format violation."""
    type: ViolationType
    message: str
    suggestion: str
    severity: str  # "error", "warning"


class ViolationDetector:
    """Detects message format violations."""
    
    def __init__(self, config):
        """Initialize violation detector."""
        self.config = config
        self.brand_codes = config.BRAND_CODES.split(',')
    
    def detect_task_allocation_violations(self, text: str, user_id: int) -> List[Violation]:
        """
        Detect violations in task allocation messages.
        Returns list of violations found.
        """
        violations = []
        
        # Check if message looks like it's trying to create a task
        has_mention = '@' in text
        has_brackets = '[' in text and ']' in text
        
        if not has_mention and not has_brackets:
            # Probably not a task message
            return []
        
        # 1. Check for [TICKET] or ticket format
        ticket_pattern = r'\[([A-Z]{2}-\d{4}-\d+|TICKET)\]'
        ticket_match = re.search(ticket_pattern, text)
        
        if not ticket_match:
            # Check if they forgot brackets
            if 'TICKET' in text.upper() or re.search(r'[A-Z]{2}-\d{4}-\d+', text):
                violations.append(Violation(
                    type=ViolationType.MISSING_BRACKETS,
                    message="Ticket ID must be in square brackets",
                    suggestion="Use [TICKET] or [PV-2404-1] format",
                    severity="error"
                ))
            else:
                violations.append(Violation(
                    type=ViolationType.INVALID_TICKET_FORMAT,
                    message="Missing ticket ID",
                    suggestion="Start message with [TICKET] or [PV-2404-1]",
                    severity="error"
                ))
        else:
            # Validate ticket format if not [TICKET]
            ticket_content = ticket_match.group(1)
            if ticket_content != "TICKET":
                # Check brand code
                brand = ticket_content.split('-')[0]
                if brand not in self.brand_codes:
                    violations.append(Violation(
                        type=ViolationType.INVALID_BRAND_CODE,
                        message=f"Invalid brand code: {brand}",
                        suggestion=f"Valid codes: {', '.join(self.brand_codes)}",
                        severity="error"
                    ))
                
                # Check format: XX-YYMM-N
                if not re.match(r'^[A-Z]{2}-\d{4}-\d+$', ticket_content):
                    violations.append(Violation(
                        type=ViolationType.INVALID_TICKET_FORMAT,
                        message="Invalid ticket format",
                        suggestion="Use format: [BRAND-YYMM-NUMBER] e.g., [PV-2404-1]",
                        severity="error"
                    ))
        
        # 2. Check for @mention
        mention_pattern = r'@(\w+)'
        mention_match = re.search(mention_pattern, text)
        
        if not mention_match:
            if has_brackets:  # Only flag if they're trying to create a task
                violations.append(Violation(
                    type=ViolationType.MISSING_MENTION,
                    message="Missing assignee mention",
                    suggestion="Include @username after ticket ID",
                    severity="error"
                ))
        
        # 3. Check for task description
        if ticket_match and mention_match:
            # Extract everything after the mention
            mention_pos = text.find(mention_match.group(0))
            description = text[mention_pos + len(mention_match.group(0)):].strip()
            
            if not description or len(description) < 3:
                violations.append(Violation(
                    type=ViolationType.MISSING_DESCRIPTION,
                    message="Task description is too short or missing",
                    suggestion="Add a clear description of what needs to be done",
                    severity="warning"
                ))
        
        # 4. Check user permissions (if config has role info)
        # This would require checking if user_id is in authorized roles
        # Skipping for now as it requires user role lookup
        
        return violations
    
    def detect_qa_submission_violations(self, text: str) -> List[Violation]:
        """
        Detect violations in QA submission messages.
        Format: [PV-2404-1][PV][Asset description]
        """
        violations = []
        
        # Check for QA submission pattern
        qa_pattern = r'\[([A-Z]{2}-\d{4}-\d+)\]\[([A-Z]{2})\]\[(.+?)\]'
        qa_match = re.match(qa_pattern, text.strip())
        
        if not qa_match:
            # Check if they're trying to submit QA but format is wrong
            if text.count('[') >= 2 and text.count(']') >= 2:
                violations.append(Violation(
                    type=ViolationType.MALFORMED_QA_SUBMISSION,
                    message="Invalid QA submission format",
                    suggestion="Use format: [TICKET][BRAND][Description]\nExample: [PV-2404-1][PV][Video thumbnail]",
                    severity="error"
                ))
        else:
            # Validate brand code
            ticket = qa_match.group(1)
            brand = qa_match.group(2)
            description = qa_match.group(3)
            
            if brand not in self.brand_codes:
                violations.append(Violation(
                    type=ViolationType.INVALID_BRAND_CODE,
                    message=f"Invalid brand code: {brand}",
                    suggestion=f"Valid codes: {', '.join(self.brand_codes)}",
                    severity="error"
                ))
            
            if not description or len(description) < 3:
                violations.append(Violation(
                    type=ViolationType.MISSING_DESCRIPTION,
                    message="Asset description is too short",
                    suggestion="Provide a clear description of what was created",
                    severity="warning"
                ))
        
        return violations
    
    def format_violation_message(self, violations: List[Violation]) -> str:
        """Format violations into a user-friendly message."""
        if not violations:
            return ""
        
        error_count = sum(1 for v in violations if v.severity == "error")
        warning_count = sum(1 for v in violations if v.severity == "warning")
        
        message = "⚠️ **Message Format Issues Detected**\n\n"
        
        if error_count > 0:
            message += f"❌ **{error_count} Error(s):**\n"
            for v in violations:
                if v.severity == "error":
                    message += f"• {v.message}\n"
                    message += f"  💡 {v.suggestion}\n\n"
        
        if warning_count > 0:
            message += f"⚠️ **{warning_count} Warning(s):**\n"
            for v in violations:
                if v.severity == "warning":
                    message += f"• {v.message}\n"
                    message += f"  💡 {v.suggestion}\n\n"
        
        message += "📄 See pinned message for correct format examples."
        
        return message
