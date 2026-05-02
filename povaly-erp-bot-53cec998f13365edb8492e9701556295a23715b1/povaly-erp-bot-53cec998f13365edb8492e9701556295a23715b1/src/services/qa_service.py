"""QA service for quality assurance workflow."""

import logging
from datetime import datetime
from typing import Optional

from src.data.models import QASubmission, QAStatus, TaskState
from src.data.repositories import TaskRepository, QARepository
from src.core.state.state_engine import StateEngine

logger = logging.getLogger(__name__)


class QAService:
    """Service for QA workflow operations."""
    
    def __init__(
        self,
        task_repo: TaskRepository,
        qa_repo: QARepository,
        state_engine: StateEngine
    ):
        """Initialize QA service."""
        self.task_repo = task_repo
        self.qa_repo = qa_repo
        self.state_engine = state_engine
    
    async def submit_for_qa(
        self,
        ticket: str,
        brand: str,
        asset: str,
        submitter_id: int,
        message_id: int
    ) -> Optional[QASubmission]:
        """
        Submit a task for QA review.
        
        Args:
            ticket: Task ticket ID
            brand: Brand name or code (e.g., "Povaly", "POV", "GSMAura", "GSM")
            asset: Asset description
            submitter_id: User ID of submitter
            message_id: Telegram message ID
        
        Returns:
            Created QA submission or None if submission failed
        """
        from src.core.brand_mapper import BrandMapper
        
        # Convert brand name to code if needed
        brand_mapper = BrandMapper()
        brand_code = brand_mapper.get_code(brand)
        
        if not brand_code:
            logger.warning(f"Invalid brand: {brand}")
            return None
        
        # Verify task exists
        task = await self.task_repo.get_task(ticket)
        if not task:
            logger.warning(f"Task {ticket} not found for QA submission")
            return None
        
        # Verify submitter is the assignee
        if task.assignee_id != submitter_id:
            logger.warning(
                f"User {submitter_id} attempted to submit QA for task {ticket} "
                f"assigned to {task.assignee_id}"
            )
            return None
        
        # Create QA submission with brand code
        submission = QASubmission(
            id=None,
            ticket=ticket,
            brand=brand_code,
            asset=asset,
            submitter_id=submitter_id,
            submitted_at=datetime.now(),
            message_id=message_id,
            status=QAStatus.PENDING
        )
        
        await self.qa_repo.create_submission(submission)
        logger.info(f"QA submission created for task {ticket} with brand {brand_code}")
        
        # Transition task state to QA_SUBMITTED
        await self.state_engine.process_qa_submission(ticket, submission.submitted_at)
        
        return submission
    
    async def approve_qa(
        self,
        ticket: str,
        reviewer_id: int
    ) -> bool:
        """
        Approve a QA submission.
        
        Args:
            ticket: Task ticket ID
            reviewer_id: User ID of reviewer
        
        Returns:
            True if approval was successful
        """
        submission = await self.qa_repo.get_submission(ticket)
        if not submission:
            logger.warning(f"QA submission not found for task {ticket}")
            return False
        
        if submission.status != QAStatus.PENDING:
            logger.warning(f"QA submission for {ticket} is not pending")
            return False
        
        # Update submission status
        reviewed_at = datetime.now()
        await self.qa_repo.update_submission_status(
            ticket,
            QAStatus.APPROVED,
            reviewer_id,
            reviewed_at
        )
        
        logger.info(f"QA approved for task {ticket} by user {reviewer_id}")
        return True
    
    async def reject_qa(
        self,
        ticket: str,
        reviewer_id: int
    ) -> bool:
        """
        Reject a QA submission.
        
        Args:
            ticket: Task ticket ID
            reviewer_id: User ID of reviewer
        
        Returns:
            True if rejection was successful
        """
        submission = await self.qa_repo.get_submission(ticket)
        if not submission:
            logger.warning(f"QA submission not found for task {ticket}")
            return False
        
        if submission.status != QAStatus.PENDING:
            logger.warning(f"QA submission for {ticket} is not pending")
            return False
        
        # Update submission status
        reviewed_at = datetime.now()
        await self.qa_repo.update_submission_status(
            ticket,
            QAStatus.REJECTED,
            reviewer_id,
            reviewed_at
        )
        
        logger.info(f"QA rejected for task {ticket} by user {reviewer_id}")
        return True
    
    async def get_pending_submissions(self):
        """Get all pending QA submissions."""
        return await self.qa_repo.get_pending_submissions()
