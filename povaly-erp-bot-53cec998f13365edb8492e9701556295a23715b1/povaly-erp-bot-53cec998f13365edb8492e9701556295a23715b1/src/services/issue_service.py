"""Issue service for Core Operations system."""

import logging
from typing import List, Optional
from datetime import datetime

from src.data.models.issue import Issue, IssueStatus, IssuePriority
from src.data.repositories.issue_repository import IssueRepository
from src.core.parser.issue_parser import IssueParser, IssueData

logger = logging.getLogger(__name__)


class IssueService:
    """Service for managing issues in Core Operations."""
    
    def __init__(self, db_adapter):
        """Initialize service."""
        self.repository = IssueRepository(db_adapter)
        self.parser = IssueParser()
    
    async def create_issue(self, issue_data: IssueData, creator_id: int, 
                          message_id: int, topic_id: int) -> Optional[Issue]:
        """
        Create a new issue.
        
        Args:
            issue_data: Parsed issue data
            creator_id: User ID who created the issue
            message_id: Telegram message ID
            topic_id: Telegram topic ID
            
        Returns:
            Created Issue object or None if failed
        """
        try:
            # Always auto-generate the next issue ticket to avoid duplicates
            issue_ticket = await self.repository.generate_issue_ticket(issue_data.ticket)
            
            # If user provided an issue_ticket, log it but use auto-generated one
            if issue_data.issue_ticket:
                if issue_data.issue_ticket != issue_ticket:
                    logger.info(f"User provided issue_ticket {issue_data.issue_ticket}, but using auto-generated {issue_ticket} to avoid duplicates")
                else:
                    logger.info(f"User-provided issue_ticket {issue_data.issue_ticket} matches auto-generated ticket")
            else:
                logger.info(f"Auto-generated issue ticket: {issue_ticket} for task {issue_data.ticket}")
            
            # TODO: Validate that the ticket exists as a task
            # This would require access to TaskService/TaskRepository
            # For now, we'll create the issue and let users handle validation
            
            # Create issue object
            issue = Issue(
                ticket=issue_data.ticket,
                issue_ticket=issue_ticket,
                title=issue_data.title,
                details=issue_data.details,
                priority=issue_data.priority,
                assignee_username=issue_data.assignee_username,
                creator_id=creator_id,
                message_id=message_id,
                topic_id=topic_id,
                status=IssueStatus.OPEN,
                created_at=datetime.now()
            )
            
            # Save to database
            success = await self.repository.create_issue(issue)
            if success:
                logger.info(f"Created issue {issue.issue_ticket} for task {issue.ticket}")
                return issue
            else:
                logger.error(f"Failed to save issue {issue.issue_ticket}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            return None
    
    async def get_issue(self, ticket: str) -> Optional[Issue]:
        """Get issue by ticket ID."""
        return await self.repository.get_issue(ticket)
    
    async def get_issue_by_message_id(self, message_id: int) -> Optional[Issue]:
        """Get issue by message ID."""
        return await self.repository.get_issue_by_message_id(message_id)
    
    async def claim_issue(self, issue_ticket: str, user_id: int) -> bool:
        """
        Claim an issue (👍 reaction).
        
        Args:
            issue_ticket: Issue ticket ID (e.g., POV260404-I1)
            user_id: User ID claiming the issue
            
        Returns:
            True if successfully claimed
        """
        try:
            issue = await self.repository.get_issue_by_issue_ticket(issue_ticket)
            if not issue:
                logger.warning(f"Issue {issue_ticket} not found for claim")
                return False
            
            if issue.is_resolved:
                logger.warning(f"Cannot claim resolved issue {issue_ticket}")
                return False
            
            # Add claim
            if issue.add_claim(user_id):
                success = await self.repository.update_issue(issue)
                if success:
                    logger.info(f"User {user_id} claimed issue {issue_ticket}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error claiming issue {issue_ticket}: {e}")
            return False
    
    async def unclaim_issue(self, issue_ticket: str, user_id: int) -> bool:
        """
        Remove claim from issue (remove 👍 reaction).
        
        Args:
            issue_ticket: Issue ticket ID (e.g., POV260404-I1)
            user_id: User ID removing claim
            
        Returns:
            True if successfully unclaimed
        """
        try:
            issue = await self.repository.get_issue_by_issue_ticket(issue_ticket)
            if not issue:
                logger.warning(f"Issue {issue_ticket} not found for unclaim")
                return False
            
            # Remove claim
            if issue.remove_claim(user_id):
                success = await self.repository.update_issue(issue)
                if success:
                    logger.info(f"User {user_id} unclaimed issue {issue_ticket}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error unclaiming issue {issue_ticket}: {e}")
            return False
    
    async def resolve_issue(self, issue_ticket: str, user_id: int) -> bool:
        """
        Resolve an issue (❤️ reaction).
        
        Args:
            issue_ticket: Issue ticket ID (e.g., POV260404-I1)
            user_id: User ID resolving the issue
            
        Returns:
            True if successfully resolved
        """
        try:
            issue = await self.repository.get_issue_by_issue_ticket(issue_ticket)
            if not issue:
                logger.warning(f"Issue {issue_ticket} not found for resolve")
                return False
            
            if issue.is_resolved:
                logger.warning(f"Issue {issue_ticket} already resolved")
                return False
            
            # Resolve issue
            if issue.resolve(user_id):
                success = await self.repository.update_issue(issue)
                if success:
                    logger.info(f"User {user_id} resolved issue {issue_ticket}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resolving issue {issue_ticket}: {e}")
            return False
    
    async def reject_issue(self, issue_ticket: str, user_id: int) -> bool:
        """
        Reject an issue as invalid (👎 reaction).
        
        Args:
            issue_ticket: Issue ticket ID (e.g., POV260404-I1)
            user_id: User ID rejecting the issue
            
        Returns:
            True if successfully rejected
        """
        try:
            issue = await self.repository.get_issue_by_issue_ticket(issue_ticket)
            if not issue:
                logger.warning(f"Issue {issue_ticket} not found for reject")
                return False
            
            # Reject issue
            if issue.reject(user_id):
                success = await self.repository.update_issue(issue)
                if success:
                    logger.info(f"User {user_id} rejected issue {issue_ticket}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error rejecting issue {issue_ticket}: {e}")
            return False
    
    async def get_user_issues(self, user_id: int, status_filter: Optional[IssueStatus] = None) -> List[Issue]:
        """Get all issues claimed by a user."""
        return await self.repository.get_issues_by_user(user_id, status_filter)
    
    async def get_user_created_issues(self, user_id: int, status_filter: Optional[IssueStatus] = None) -> List[Issue]:
        """Get all issues created by a user."""
        return await self.repository.get_issues_by_creator(user_id, status_filter)
    
    async def get_open_issues(self) -> List[Issue]:
        """Get all unresolved issues."""
        return await self.repository.get_open_issues()
    
    async def get_unresolved_claimed_issues(self) -> List[Issue]:
        """Get issues that are claimed but not resolved."""
        return await self.repository.get_unresolved_claimed_issues()
    
    async def get_inactive_issues(self) -> List[Issue]:
        """Get issues with no claims."""
        return await self.repository.get_inactive_issues()
    
    async def get_overdue_issues(self, hours: int = 2) -> List[Issue]:
        """Get issues that are overdue for escalation."""
        return await self.repository.get_overdue_issues(hours)
    
    async def get_issues_needing_reminder(self, hours: int = 4) -> List[Issue]:
        """Get claimed issues that need reminder."""
        return await self.repository.get_issues_needing_reminder(hours)
    
    async def mark_escalated(self, ticket: str) -> bool:
        """Mark issue as escalated."""
        try:
            issue = await self.repository.get_issue(ticket)
            if not issue:
                logger.warning(f"Cannot mark escalated - issue {ticket} not found")
                return False
            
            logger.debug(f"Before mark_escalated: {ticket} - escalation_sent={issue.escalation_sent}")
            
            if issue.mark_escalated():
                success = await self.repository.update_issue(issue)
                if success:
                    logger.info(f"✅ Marked issue {ticket} (issue_ticket={issue.issue_ticket}) as escalated")
                    return True
                else:
                    logger.error(f"❌ Failed to update issue {ticket} in database")
            else:
                logger.warning(f"Issue {ticket} already marked as escalated")
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking issue {ticket} as escalated: {e}", exc_info=True)
            return False
            logger.error(f"Error marking issue {ticket} as escalated: {e}")
            return False
    
    async def mark_reminder_sent(self, ticket: str) -> bool:
        """Mark that reminder was sent for issue."""
        try:
            issue = await self.repository.get_issue(ticket)
            if not issue:
                return False
            
            issue.reminder_sent = True
            success = await self.repository.update_issue(issue)
            if success:
                logger.info(f"Marked reminder sent for issue {ticket}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking reminder sent for issue {ticket}: {e}")
            return False
    
    def parse_issue_message(self, text: str) -> Optional[IssueData]:
        """Parse issue data from message text."""
        return self.parser.parse_issue(text)
    
    def validate_issue_format(self, text: str) -> tuple[bool, str]:
        """Validate issue message format."""
        return self.parser.validate_format(text)
    
    def is_issue_message(self, text: str) -> bool:
        """Check if message looks like an issue."""
        return self.parser.is_issue_format(text)
    
    def extract_ticket_from_text(self, text: str) -> Optional[str]:
        """Extract ticket ID from any text."""
        return self.parser.extract_ticket_from_text(text)
    
    def format_issue_summary(self, issue: Issue) -> str:
        """Format issue for display."""
        status_emoji = {
            IssueStatus.OPEN: "🔴",
            IssueStatus.IN_PROGRESS: "🟡",
            IssueStatus.RESOLVED: "✅",
            IssueStatus.INVALID: "❌",
            IssueStatus.ESCALATED: "🚨"
        }
        
        priority_emoji = {
            IssuePriority.LOW: "🟢",
            IssuePriority.MEDIUM: "🟡",
            IssuePriority.HIGH: "🟠",
            IssuePriority.CRITICAL: "🔴"
        }
        
        status = status_emoji.get(issue.status, "❓")
        priority = priority_emoji.get(issue.priority, "❓")
        
        summary = f"{status} **{issue.ticket}** - {issue.title}\n"
        summary += f"{priority} Priority: {issue.priority.value}\n"
        
        if issue.assignee_username:
            summary += f"👤 Assigned: @{issue.assignee_username}\n"
        
        if issue.claimed_by:
            handlers = ", ".join([f"<{uid}>" for uid in issue.claimed_by])
            summary += f"👍 Claimed by: {handlers}\n"
        
        if issue.created_at:
            summary += f"📅 Created: {issue.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        return summary.strip()