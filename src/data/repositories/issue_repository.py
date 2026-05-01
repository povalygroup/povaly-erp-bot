"""Issue repository for Core Operations system."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from src.data.models.issue import Issue, IssueStatus, IssuePriority

logger = logging.getLogger(__name__)


class IssueRepository:
    """Repository for managing issues."""

    def __init__(self, db_adapter):
        """Initialize repository."""
        self.db_adapter = db_adapter
        self.table_name = "issues"

    async def create_issue(self, issue: Issue) -> bool:
        """Create a new issue."""
        try:
            query = """
            INSERT INTO issues (
                ticket, issue_ticket, title, details, priority, assignee_username,
                creator_id, message_id, topic_id, status,
                created_at, claimed_by, escalation_sent, reminder_sent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                issue.ticket,
                issue.issue_ticket,
                issue.title,
                issue.details,
                issue.priority.value,
                issue.assignee_username,
                issue.creator_id,
                issue.message_id,
                issue.topic_id,
                issue.status.value,
                issue.created_at.isoformat() if issue.created_at else None,
                ','.join(map(str, issue.claimed_by)) if issue.claimed_by else '',
                issue.escalation_sent,
                issue.reminder_sent
            )
            
            result = await self.db_adapter.execute_query(query, params)
            logger.info(f"Created issue {issue.issue_ticket} for task {issue.ticket}")
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to create issue {issue.issue_ticket}: {e}")
            return False

    async def get_issue(self, ticket: str) -> Optional[Issue]:
        """Get issue by ticket ID."""
        try:
            query = "SELECT * FROM issues WHERE ticket = ?"
            result = await self.db_adapter.fetch_one(query, (ticket,))
            
            if result:
                return self._row_to_issue(result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get issue {ticket}: {e}")
            return None

    async def get_issue_by_issue_ticket(self, issue_ticket: str) -> Optional[Issue]:
        """Get issue by issue ticket ID (e.g., POV260410-I1)."""
        try:
            query = "SELECT * FROM issues WHERE issue_ticket = ?"
            result = await self.db_adapter.fetch_one(query, (issue_ticket,))
            
            if result:
                return self._row_to_issue(result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get issue by issue_ticket {issue_ticket}: {e}")
            return None

    async def generate_issue_ticket(self, task_ticket: str) -> str:
        """Generate the next issue ticket for a task (e.g., POV260410-I1, POV260410-I2)."""
        try:
            # Get all issues for this task
            query = "SELECT issue_ticket FROM issues WHERE ticket = ? ORDER BY issue_ticket DESC LIMIT 1"
            result = await self.db_adapter.fetch_one(query, (task_ticket,))
            
            if result and result.get('issue_ticket'):
                # Extract the issue number from the last issue ticket
                last_issue_ticket = result['issue_ticket']
                if '-I' in last_issue_ticket:
                    try:
                        issue_num = int(last_issue_ticket.split('-I')[1])
                        next_num = issue_num + 1
                    except (ValueError, IndexError):
                        next_num = 1
                else:
                    next_num = 1
            else:
                # First issue for this task
                next_num = 1
            
            return f"{task_ticket}-I{next_num}"
            
        except Exception as e:
            logger.error(f"Failed to generate issue ticket for {task_ticket}: {e}")
            return f"{task_ticket}-I1"  # Fallback to I1

    async def get_issue_by_message_id(self, message_id: int) -> Optional[Issue]:
        """Get issue by message ID."""
        try:
            query = "SELECT * FROM issues WHERE message_id = ?"
            result = await self.db_adapter.fetch_one(query, (message_id,))
            
            if result:
                return self._row_to_issue(result)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get issue by message_id {message_id}: {e}")
            return None

    async def update_issue(self, issue: Issue) -> bool:
        """Update an existing issue."""
        try:
            query = """
            UPDATE issues SET
                title = ?, details = ?, priority = ?, assignee_username = ?,
                status = ?, claimed_at = ?, resolved_at = ?, escalated_at = ?,
                claimed_by = ?, resolved_by = ?, rejected_by = ?,
                escalation_sent = ?, reminder_sent = ?
            WHERE issue_ticket = ?
            """
            
            params = (
                issue.title,
                issue.details,
                issue.priority.value,
                issue.assignee_username,
                issue.status.value,
                issue.claimed_at.isoformat() if issue.claimed_at else None,
                issue.resolved_at.isoformat() if issue.resolved_at else None,
                issue.escalated_at.isoformat() if issue.escalated_at else None,
                ','.join(map(str, issue.claimed_by)) if issue.claimed_by else '',
                issue.resolved_by,
                issue.rejected_by,
                issue.escalation_sent,
                issue.reminder_sent,
                issue.issue_ticket
            )
            
            result = await self.db_adapter.execute_query(query, params)
            logger.info(f"Updated issue {issue.issue_ticket}")
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to update issue {issue.issue_ticket}: {e}")
            return False

    async def get_issues_by_user(self, user_id: int, status_filter: Optional[IssueStatus] = None) -> List[Issue]:
        """Get all issues claimed by a user."""
        try:
            query = "SELECT * FROM issues WHERE claimed_by LIKE ?"
            params = (f"%{user_id}%",)
            
            if status_filter:
                query += " AND status = ?"
                params = (f"%{user_id}%", status_filter.value)
            
            results = await self.db_adapter.fetch_all(query, params)
            issues = []
            
            for row in results:
                issue = self._row_to_issue(row)
                # Verify user is actually in claimed_by list (not just substring match)
                if user_id in issue.claimed_by:
                    issues.append(issue)
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to get issues for user {user_id}: {e}")
            return []

    async def get_issues_by_creator(self, user_id: int, status_filter: Optional[IssueStatus] = None) -> List[Issue]:
        """Get all issues created by a user."""
        try:
            query = "SELECT * FROM issues WHERE creator_id = ?"
            params = (user_id,)
            
            if status_filter:
                query += " AND status = ?"
                params = (user_id, status_filter.value)
            
            query += " ORDER BY created_at DESC"
            
            results = await self.db_adapter.fetch_all(query, params)
            return [self._row_to_issue(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get issues created by user {user_id}: {e}")
            return []

    async def get_open_issues(self) -> List[Issue]:
        """Get all unresolved issues."""
        try:
            query = "SELECT * FROM issues WHERE status != ? ORDER BY created_at ASC"
            results = await self.db_adapter.fetch_all(query, (IssueStatus.RESOLVED.value,))
            
            return [self._row_to_issue(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get open issues: {e}")
            return []

    async def get_unresolved_claimed_issues(self) -> List[Issue]:
        """Get issues that are claimed but not resolved."""
        try:
            query = """
            SELECT * FROM issues 
            WHERE status = ? AND claimed_by != '' 
            ORDER BY claimed_at ASC
            """
            results = await self.db_adapter.fetch_all(query, (IssueStatus.IN_PROGRESS.value,))
            
            return [self._row_to_issue(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get unresolved claimed issues: {e}")
            return []

    async def get_inactive_issues(self) -> List[Issue]:
        """Get issues with no claims."""
        try:
            query = """
            SELECT * FROM issues 
            WHERE status = ? AND (claimed_by = '' OR claimed_by IS NULL)
            ORDER BY created_at ASC
            """
            results = await self.db_adapter.fetch_all(query, (IssueStatus.OPEN.value,))
            
            return [self._row_to_issue(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get inactive issues: {e}")
            return []

    async def get_overdue_issues(self, hours: int = 2) -> List[Issue]:
        """Get issues that are overdue for escalation."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            query = """
            SELECT * FROM issues 
            WHERE status != ? AND status != ? 
            AND escalation_sent = 0 
            AND created_at < ?
            ORDER BY created_at ASC
            """
            
            params = (
                IssueStatus.RESOLVED.value,
                IssueStatus.INVALID.value,
                cutoff_time.isoformat()
            )
            
            results = await self.db_adapter.fetch_all(query, params)
            return [self._row_to_issue(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get overdue issues: {e}")
            return []

    async def get_issues_needing_reminder(self, hours: int = 4) -> List[Issue]:
        """Get claimed issues that need reminder."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            query = """
            SELECT * FROM issues 
            WHERE status = ? 
            AND claimed_by != '' 
            AND reminder_sent = 0 
            AND claimed_at < ?
            ORDER BY claimed_at ASC
            """
            
            params = (
                IssueStatus.IN_PROGRESS.value,
                cutoff_time.isoformat()
            )
            
            results = await self.db_adapter.fetch_all(query, params)
            return [self._row_to_issue(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get issues needing reminder: {e}")
            return []

    async def delete_issue(self, issue_ticket: str) -> bool:
        """Delete an issue by issue_ticket."""
        try:
            query = "DELETE FROM issues WHERE issue_ticket = ?"
            result = await self.db_adapter.execute_query(query, (issue_ticket,))
            logger.info(f"Deleted issue {issue_ticket}")
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to delete issue {issue_ticket}: {e}")
            return False

    def _row_to_issue(self, row) -> Issue:
        """Convert database row to Issue object."""
        # Parse claimed_by string back to list
        claimed_by_str = row.get('claimed_by', '')
        claimed_by = []
        if claimed_by_str:
            try:
                claimed_by = [int(x) for x in claimed_by_str.split(',') if x.strip()]
            except ValueError:
                claimed_by = []
        
        # Parse datetime fields
        created_at = None
        if row.get('created_at'):
            try:
                created_at = datetime.fromisoformat(row['created_at'])
            except ValueError:
                created_at = datetime.now()
        
        claimed_at = None
        if row.get('claimed_at'):
            try:
                claimed_at = datetime.fromisoformat(row['claimed_at'])
            except ValueError:
                pass
        
        resolved_at = None
        if row.get('resolved_at'):
            try:
                resolved_at = datetime.fromisoformat(row['resolved_at'])
            except ValueError:
                pass
        
        escalated_at = None
        if row.get('escalated_at'):
            try:
                escalated_at = datetime.fromisoformat(row['escalated_at'])
            except ValueError:
                pass
        
        return Issue(
            ticket=row['ticket'],
            issue_ticket=row.get('issue_ticket', row['ticket']),  # Fallback for backward compatibility
            title=row['title'],
            details=row['details'],
            priority=IssuePriority(row['priority']),
            assignee_username=row.get('assignee_username'),
            creator_id=row.get('creator_id', 0),
            message_id=row.get('message_id', 0),
            topic_id=row.get('topic_id', 0),
            status=IssueStatus(row.get('status', 'open')),
            created_at=created_at,
            claimed_at=claimed_at,
            resolved_at=resolved_at,
            escalated_at=escalated_at,
            claimed_by=claimed_by,
            resolved_by=row.get('resolved_by'),
            rejected_by=row.get('rejected_by'),
            escalation_sent=bool(row.get('escalation_sent', False)),
            reminder_sent=bool(row.get('reminder_sent', False))
        )