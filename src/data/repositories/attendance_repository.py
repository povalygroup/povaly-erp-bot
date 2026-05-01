"""Attendance repository for data access."""

from typing import Optional, List
from datetime import date, datetime

from src.data.models import Attendance, LeaveRequest, LeaveStatus


class AttendanceRepository:
    """Repository for attendance-related data operations."""
    
    def __init__(self, db):
        """Initialize with database adapter."""
        self.db = db
    
    async def create_attendance(self, attendance: Attendance) -> None:
        """Create a new attendance record."""
        await self.db.insert_attendance(attendance)
    
    async def get_attendance(self, user_id: int, date: date) -> Optional[Attendance]:
        """Get attendance record for a user on a specific date."""
        return await self.db.get_attendance_by_user_date(user_id, date)
    
    async def update_checkout(
        self, 
        user_id: int, 
        date: date, 
        checkout_time: datetime, 
        is_auto: bool = False
    ) -> None:
        """Update checkout time for an attendance record."""
        await self.db.update_attendance_checkout(user_id, date, checkout_time, is_auto)
    
    async def get_attendance_by_user(self, user_id: int, start_date: date, end_date: date) -> List[Attendance]:
        """Get attendance records for a user in a date range."""
        return await self.db.get_attendance_by_user_range(user_id, start_date, end_date)
    
    async def get_late_checkins(self, user_id: int, start_date: date, end_date: date) -> List[Attendance]:
        """Get late check-ins for a user in a date range."""
        return await self.db.get_late_checkins(user_id, start_date, end_date)
    
    async def create_leave_request(self, leave_request: LeaveRequest) -> None:
        """Create a new leave request."""
        await self.db.insert_leave_request(leave_request)
    
    async def get_leave_request(self, request_id: int) -> Optional[LeaveRequest]:
        """Get leave request by ID."""
        return await self.db.get_leave_request_by_id(request_id)
    
    async def update_leave_status(
        self, 
        request_id: int, 
        status: LeaveStatus, 
        reviewed_by: int, 
        reviewed_at: datetime
    ) -> None:
        """Update leave request status."""
        await self.db.update_leave_request_status(request_id, status, reviewed_by, reviewed_at)
    
    async def get_pending_leave_requests(self) -> List[LeaveRequest]:
        """Get all pending leave requests."""
        return await self.db.get_leave_requests_by_status(LeaveStatus.PENDING)
    
    async def get_leave_requests_by_user(self, user_id: int) -> List[LeaveRequest]:
        """Get leave requests for a user."""
        return await self.db.get_leave_requests_by_user(user_id)
