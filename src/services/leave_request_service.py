"""Leave request service for managing employee leave."""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple
from src.data.models.leave_request import LeaveRequest, LeaveStatus
from src.data.models.task import TaskState

logger = logging.getLogger(__name__)


class LeaveRequestService:
    """Service for managing leave requests."""
    
    def __init__(self, attendance_repo, user_repo, task_service, config):
        """Initialize leave request service."""
        self.attendance_repo = attendance_repo
        self.user_repo = user_repo
        self.task_service = task_service
        self.config = config
    
    async def create_leave_request(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        reason: str,
        message_id: int,
        replacement_user_id: Optional[int] = None
    ) -> Tuple[bool, str, Optional[LeaveRequest]]:
        """
        Create a new leave request.
        
        Returns:
            (success: bool, message: str, leave_request: Optional[LeaveRequest])
        """
        try:
            # Validate dates
            if start_date > end_date:
                return False, "Start date must be before end date", None
            
            if start_date < date.today():
                return False, "Cannot request leave for past dates", None
            
            # Check minimum notice period
            days_notice = (start_date - date.today()).days
            if days_notice < self.config.LEAVE_REQUEST_MIN_NOTICE_DAYS:
                return False, f"Minimum {self.config.LEAVE_REQUEST_MIN_NOTICE_DAYS} days notice required", None
            
            # Check maximum duration
            duration = (end_date - start_date).days + 1
            if duration > self.config.LEAVE_REQUEST_MAX_DURATION_DAYS:
                return False, f"Maximum leave duration is {self.config.LEAVE_REQUEST_MAX_DURATION_DAYS} days", None
            
            # Check for overlapping requests
            if not self.config.LEAVE_REQUEST_ALLOW_OVERLAPPING:
                existing_requests = await self.attendance_repo.get_leave_requests_by_user(user_id)
                for req in existing_requests:
                    if req.status == LeaveStatus.APPROVED:
                        # Check if dates overlap
                        if not (end_date < req.start_date or start_date > req.end_date):
                            return False, f"You already have approved leave from {req.start_date} to {req.end_date}", None
            
            # Check if replacement is required
            if self.config.LEAVE_REQUEST_REQUIRE_REPLACEMENT and not replacement_user_id:
                return False, "Replacement user is required for leave requests", None
            
            # Create leave request
            leave_request = LeaveRequest(
                id=None,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                status=LeaveStatus.PENDING,
                requested_at=datetime.now(),
                message_id=message_id,
                replacement_user_id=replacement_user_id,
                task_handover_ids=None,
                is_notified=False
            )
            
            await self.attendance_repo.create_leave_request(leave_request)
            logger.info(f"✅ Created leave request for user {user_id} from {start_date} to {end_date}")
            
            return True, "Leave request created successfully", leave_request
        
        except Exception as e:
            logger.error(f"Error creating leave request: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    async def approve_leave_request(
        self,
        request_id: int,
        reviewed_by: int
    ) -> Tuple[bool, str]:
        """
        Approve a leave request.
        
        Returns:
            (success: bool, message: str)
        """
        try:
            leave_request = await self.attendance_repo.get_leave_request(request_id)
            if not leave_request:
                return False, "Leave request not found"
            
            if leave_request.status != LeaveStatus.PENDING:
                return False, f"Leave request is already {leave_request.status.value}"
            
            # Update leave request status
            await self.attendance_repo.update_leave_status(
                request_id,
                LeaveStatus.APPROVED,
                reviewed_by,
                datetime.now()
            )
            
            # Mark user as on leave
            await self.user_repo.set_on_leave(
                leave_request.user_id,
                leave_request.start_date,
                leave_request.end_date
            )
            
            # Handle task reassignment if replacement specified
            if leave_request.replacement_user_id and self.config.LEAVE_REQUEST_AUTO_REASSIGN_TASKS:
                await self._reassign_tasks_to_replacement(
                    leave_request.user_id,
                    leave_request.replacement_user_id,
                    request_id
                )
            
            logger.info(f"✅ Approved leave request {request_id} for user {leave_request.user_id}")
            return True, "Leave request approved"
        
        except Exception as e:
            logger.error(f"Error approving leave request: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    async def reject_leave_request(
        self,
        request_id: int,
        reviewed_by: int
    ) -> Tuple[bool, str]:
        """
        Reject a leave request.
        
        Returns:
            (success: bool, message: str)
        """
        try:
            leave_request = await self.attendance_repo.get_leave_request(request_id)
            if not leave_request:
                return False, "Leave request not found"
            
            if leave_request.status != LeaveStatus.PENDING:
                return False, f"Leave request is already {leave_request.status.value}"
            
            # Update leave request status
            await self.attendance_repo.update_leave_status(
                request_id,
                LeaveStatus.REJECTED,
                reviewed_by,
                datetime.now()
            )
            
            logger.info(f"✅ Rejected leave request {request_id} for user {leave_request.user_id}")
            return True, "Leave request rejected"
        
        except Exception as e:
            logger.error(f"Error rejecting leave request: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    async def _reassign_tasks_to_replacement(
        self,
        original_user_id: int,
        replacement_user_id: int,
        request_id: int
    ) -> None:
        """Reassign active tasks from user on leave to replacement."""
        try:
            # Get all active tasks for the user on leave
            active_states = [
                TaskState.ASSIGNED,
                TaskState.STARTED,
                TaskState.QA_SUBMITTED,
                TaskState.REJECTED
            ]
            
            tasks_to_reassign = []
            for state in active_states:
                tasks = await self.task_service.task_repo.get_tasks_by_assignee(original_user_id, state)
                tasks_to_reassign.extend(tasks)
            
            if not tasks_to_reassign:
                logger.info(f"No active tasks to reassign for user {original_user_id}")
                return
            
            # Reassign each task
            reassigned_count = 0
            for task in tasks_to_reassign:
                try:
                    task.assignee_id = replacement_user_id
                    await self.task_service.task_repo.db.conn.execute(
                        "UPDATE tasks SET assignee_id = ? WHERE ticket = ?",
                        (replacement_user_id, task.ticket)
                    )
                    await self.task_service.task_repo.db.conn.commit()
                    reassigned_count += 1
                except Exception as e:
                    logger.warning(f"Failed to reassign task {task.ticket}: {e}")
            
            logger.info(f"✅ Reassigned {reassigned_count} tasks from user {original_user_id} to {replacement_user_id}")
        
        except Exception as e:
            logger.error(f"Error reassigning tasks: {e}", exc_info=True)
    
    async def is_user_on_leave(self, user_id: int, check_date: Optional[date] = None) -> bool:
        """Check if user is on leave on a specific date."""
        try:
            if check_date is None:
                check_date = date.today()
            
            user = await self.user_repo.get_user(user_id)
            if not user or not user.is_on_leave:
                return False
            
            if user.leave_start and user.leave_end:
                return user.leave_start.date() <= check_date <= user.leave_end.date()
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking if user is on leave: {e}")
            return False
    
    async def clear_expired_leave(self) -> int:
        """Clear leave status for users whose leave has ended."""
        try:
            all_users = await self.user_repo.get_all_users()
            cleared_count = 0
            
            for user in all_users:
                if user.is_on_leave and user.leave_end:
                    if user.leave_end.date() < date.today():
                        await self.user_repo.clear_leave(user.user_id)
                        cleared_count += 1
                        logger.info(f"Cleared leave status for user {user.user_id}")
            
            return cleared_count
        
        except Exception as e:
            logger.error(f"Error clearing expired leave: {e}")
            return 0
