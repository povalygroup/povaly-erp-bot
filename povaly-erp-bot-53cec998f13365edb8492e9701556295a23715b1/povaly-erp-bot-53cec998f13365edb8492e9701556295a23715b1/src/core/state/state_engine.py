"""State engine for managing task state transitions."""

import logging
from datetime import datetime
from typing import Optional

from src.data.models import Task, TaskState, TaskReaction
from src.data.repositories import TaskRepository

logger = logging.getLogger(__name__)


class StateEngine:
    """Manages task state transitions based on events."""
    
    def __init__(self, task_repo: TaskRepository):
        """Initialize state engine with task repository."""
        self.task_repo = task_repo
    
    async def process_thumbs_up_reaction(self, ticket: str, user_id: int, timestamp: datetime) -> bool:
        """
        Process 👍 reaction - transitions ASSIGNED → STARTED.
        
        Args:
            ticket: Task ticket ID
            user_id: User who added reaction
            timestamp: When reaction was added
        
        Returns:
            True if state was transitioned, False otherwise
        """
        task = await self.task_repo.get_task(ticket)
        if not task:
            logger.warning(f"Task {ticket} not found for 👍 reaction")
            return False
        
        # Only transition if task is in ASSIGNED state
        if task.state != TaskState.ASSIGNED:
            logger.debug(f"Task {ticket} is in {task.state}, not transitioning on 👍")
            return False
        
        # Check if this is the first 👍 reaction
        first_reaction = await self.task_repo.get_first_reaction(ticket, "👍")
        if first_reaction and first_reaction.timestamp < timestamp:
            logger.debug(f"Task {ticket} already has earlier 👍 reaction")
            return False
        
        # Transition to STARTED
        await self.task_repo.update_task_state(ticket, TaskState.STARTED, timestamp)
        logger.info(f"Task {ticket} transitioned ASSIGNED → STARTED by user {user_id}")
        return True
    
    async def process_heart_reaction(self, ticket: str, user_id: int, timestamp: datetime) -> bool:
        """
        Process ❤️ reaction - transitions QA_SUBMITTED → APPROVED.
        
        Args:
            ticket: Task ticket ID
            user_id: User who added reaction (QA reviewer)
            timestamp: When reaction was added
        
        Returns:
            True if state was transitioned, False otherwise
        """
        task = await self.task_repo.get_task(ticket)
        if not task:
            logger.warning(f"Task {ticket} not found for ❤️ reaction")
            return False
        
        # Only transition if task is in QA_SUBMITTED state
        if task.state != TaskState.QA_SUBMITTED:
            logger.debug(f"Task {ticket} is in {task.state}, not transitioning on ❤️")
            return False
        
        # Transition to APPROVED
        await self.task_repo.update_task_state(ticket, TaskState.APPROVED, timestamp)
        logger.info(f"Task {ticket} transitioned QA_SUBMITTED → APPROVED by user {user_id}")
        return True
    
    async def process_thumbs_down_reaction(self, ticket: str, user_id: int, timestamp: datetime) -> bool:
        """
        Process 👎 reaction - transitions QA_SUBMITTED → REJECTED.
        
        Args:
            ticket: Task ticket ID
            user_id: User who added reaction (QA reviewer)
            timestamp: When reaction was added
        
        Returns:
            True if state was transitioned, False otherwise
        """
        task = await self.task_repo.get_task(ticket)
        if not task:
            logger.warning(f"Task {ticket} not found for 👎 reaction")
            return False
        
        # Only transition if task is in QA_SUBMITTED state
        if task.state != TaskState.QA_SUBMITTED:
            logger.debug(f"Task {ticket} is in {task.state}, not transitioning on 👎")
            return False
        
        # Transition to REJECTED
        await self.task_repo.update_task_state(ticket, TaskState.REJECTED, timestamp)
        logger.info(f"Task {ticket} transitioned QA_SUBMITTED → REJECTED by user {user_id}")
        return True
    
    async def process_fire_reaction(self, ticket: str, user_id: int, timestamp: datetime) -> bool:
        """
        Process 🔥 reaction - marks task as exempt from daily carryover.
        
        Args:
            ticket: Task ticket ID
            user_id: User who added reaction (must be authorized)
            timestamp: When reaction was added
        
        Returns:
            True if exemption was applied, False otherwise
        """
        task = await self.task_repo.get_task(ticket)
        if not task:
            logger.warning(f"Task {ticket} not found for 🔥 reaction")
            return False
        
        # Apply fire exemption
        await self.task_repo.update_fire_exemption(ticket, user_id, timestamp)
        logger.info(f"Task {ticket} marked with 🔥 exemption by user {user_id}")
        return True
    
    async def process_qa_submission(self, ticket: str, timestamp: datetime) -> bool:
        """
        Process QA submission - transitions STARTED → QA_SUBMITTED.
        
        Args:
            ticket: Task ticket ID
            timestamp: When QA was submitted
        
        Returns:
            True if state was transitioned, False otherwise
        """
        task = await self.task_repo.get_task(ticket)
        if not task:
            logger.warning(f"Task {ticket} not found for QA submission")
            return False
        
        # Only transition if task is in STARTED state
        if task.state != TaskState.STARTED:
            logger.debug(f"Task {ticket} is in {task.state}, not transitioning on QA submission")
            return False
        
        # Transition to QA_SUBMITTED
        await self.task_repo.update_task_state(ticket, TaskState.QA_SUBMITTED, timestamp)
        logger.info(f"Task {ticket} transitioned STARTED → QA_SUBMITTED")
        return True
    
    async def get_current_state(self, ticket: str) -> Optional[TaskState]:
        """Get current state of a task."""
        task = await self.task_repo.get_task(ticket)
        return task.state if task else None
    
    def validate_transition(self, current_state: TaskState, event: str) -> bool:
        """
        Validate if a state transition is allowed.
        
        Args:
            current_state: Current task state
            event: Event triggering transition (e.g., "👍", "QA_SUBMISSION", "❤️", "👎")
        
        Returns:
            True if transition is valid, False otherwise
        """
        valid_transitions = {
            TaskState.ASSIGNED: ["👍"],
            TaskState.STARTED: ["QA_SUBMISSION"],
            TaskState.QA_SUBMITTED: ["❤️", "👎"],
            TaskState.REJECTED: ["QA_SUBMISSION"],  # Can resubmit after rejection
        }
        
        allowed_events = valid_transitions.get(current_state, [])
        return event in allowed_events
