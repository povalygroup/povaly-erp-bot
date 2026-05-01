"""QA repository for data access."""

from typing import Optional, List
from datetime import datetime

from src.data.models import QASubmission, QAStatus


class QARepository:
    """Repository for QA-related data operations."""
    
    def __init__(self, db):
        """Initialize with database adapter."""
        self.db = db
    
    async def create_submission(self, submission: QASubmission) -> None:
        """Create a new QA submission."""
        await self.db.insert_qa_submission(submission)
    
    async def get_submission(self, ticket: str) -> Optional[QASubmission]:
        """Get QA submission by ticket."""
        return await self.db.get_qa_submission_by_ticket(ticket)
    
    async def get_submission_by_message_id(self, message_id: int) -> Optional[QASubmission]:
        """Get QA submission by message ID."""
        return await self.db.get_qa_submission_by_message_id(message_id)
    
    async def update_submission_status(
        self, 
        ticket: str, 
        status: QAStatus, 
        reviewed_by: int, 
        reviewed_at: datetime
    ) -> None:
        """Update QA submission status."""
        await self.db.update_qa_submission_status(ticket, status, reviewed_by, reviewed_at)
    
    async def get_pending_submissions(self) -> List[QASubmission]:
        """Get all pending QA submissions."""
        return await self.db.get_qa_submissions_by_status(QAStatus.PENDING)
    
    async def get_submissions_by_status(self, status: QAStatus) -> List[QASubmission]:
        """Get QA submissions by status."""
        return await self.db.get_qa_submissions_by_status(status)
    
    async def get_submissions_by_submitter(self, submitter_id: int) -> List[QASubmission]:
        """Get QA submissions by submitter."""
        return await self.db.get_qa_submissions_by_submitter(submitter_id)
    
    async def get_submissions_older_than(self, hours: int) -> List[QASubmission]:
        """Get submissions older than specified hours."""
        return await self.db.get_qa_submissions_older_than(hours)
