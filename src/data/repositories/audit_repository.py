"""Audit repository for data access."""

from typing import Optional, List
from datetime import datetime

from src.data.models import AuditTrail, EventType, Report, ReportType, Violation, ViolationType


class AuditRepository:
    """Repository for audit trail and reporting data operations."""
    
    def __init__(self, db):
        """Initialize with database adapter."""
        self.db = db
    
    async def log_event(self, audit: AuditTrail) -> None:
        """Log an audit trail event."""
        await self.db.insert_audit_trail(audit)
    
    async def get_events_by_user(self, user_id: int, start_time: datetime, end_time: datetime) -> List[AuditTrail]:
        """Get audit events for a user in a time range."""
        return await self.db.get_audit_by_user(user_id, start_time, end_time)
    
    async def get_events_by_ticket(self, ticket: str) -> List[AuditTrail]:
        """Get audit events for a ticket."""
        return await self.db.get_audit_by_ticket(ticket)
    
    async def get_events_by_type(self, event_type: EventType, start_time: datetime, end_time: datetime) -> List[AuditTrail]:
        """Get audit events by type in a time range."""
        return await self.db.get_audit_by_type(event_type, start_time, end_time)
    
    async def create_report(self, report: Report) -> None:
        """Create a new report."""
        await self.db.insert_report(report)
    
    async def get_report(self, report_id: int) -> Optional[Report]:
        """Get report by ID."""
        return await self.db.get_report_by_id(report_id)
    
    async def get_reports_by_type(self, report_type: ReportType, start_date: datetime, end_date: datetime) -> List[Report]:
        """Get reports by type in a date range."""
        return await self.db.get_reports_by_type(report_type, start_date, end_date)
    
    async def get_reports_by_user(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Report]:
        """Get reports for a user in a date range."""
        return await self.db.get_reports_by_user(user_id, start_date, end_date)
    
    async def create_violation(self, violation: Violation) -> None:
        """Create a new violation record."""
        await self.db.insert_violation(violation)
    
    async def get_violations_by_user(self, user_id: int, start_time: datetime, end_time: datetime) -> List[Violation]:
        """Get violations for a user in a time range."""
        return await self.db.get_violations_by_user(user_id, start_time, end_time)
    
    async def get_violations_by_type(self, violation_type: ViolationType, start_time: datetime, end_time: datetime) -> List[Violation]:
        """Get violations by type in a time range."""
        return await self.db.get_violations_by_type(violation_type, start_time, end_time)
    
    async def count_user_violations(self, user_id: int, start_time: datetime, end_time: datetime) -> int:
        """Count violations for a user in a time range."""
        violations = await self.get_violations_by_user(user_id, start_time, end_time)
        return len(violations)
