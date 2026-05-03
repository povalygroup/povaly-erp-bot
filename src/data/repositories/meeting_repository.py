"""Meeting repository for data access."""

from typing import Optional, List
from datetime import datetime

from src.data.models import (
    Meeting,
    MeetingStatus,
    MeetingPriority,
    MeetingAttendee,
    AttendanceStatus,
    MeetingNotes,
    MeetingReaction,
)


class MeetingRepository:
    """Repository for meeting-related data operations."""
    
    def __init__(self, db):
        """Initialize with database adapter."""
        self.db = db
    
    # ============================================================================
    # MEETING OPERATIONS
    # ============================================================================
    
    async def create_meeting(self, meeting: Meeting) -> None:
        """Create a new meeting."""
        await self.db.insert_meeting(meeting)
    
    async def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get meeting by meeting ID."""
        return await self.db.get_meeting_by_id(meeting_id)
    
    async def get_meeting_by_message_id(self, message_id: int) -> Optional[Meeting]:
        """Get meeting by message ID."""
        return await self.db.get_meeting_by_message_id(message_id)
    
    async def update_meeting_status(
        self, 
        meeting_id: str, 
        status: MeetingStatus, 
        timestamp: Optional[datetime] = None
    ) -> None:
        """Update meeting status."""
        await self.db.update_meeting_status(meeting_id, status, timestamp)
    
    async def update_meeting_reminder(
        self, 
        meeting_id: str, 
        reminder_type: str,  # '24h', '1h', '15m'
        timestamp: datetime
    ) -> None:
        """Update meeting reminder timestamp."""
        await self.db.update_meeting_reminder(meeting_id, reminder_type, timestamp)
    
    async def link_meeting_notes(self, meeting_id: str, notes_message_id: int) -> None:
        """Link meeting notes message to meeting."""
        await self.db.update_meeting_notes_link(meeting_id, notes_message_id)
    
    async def cancel_meeting(
        self, 
        meeting_id: str, 
        reason: str, 
        cancelled_at: datetime
    ) -> None:
        """Cancel a meeting."""
        await self.db.cancel_meeting(meeting_id, reason, cancelled_at)
    
    async def reschedule_meeting(
        self, 
        meeting_id: str, 
        new_meeting_id: str
    ) -> None:
        """Mark meeting as rescheduled and link to new meeting."""
        await self.db.reschedule_meeting(meeting_id, new_meeting_id)
    
    async def get_upcoming_meetings(self, after_date: datetime) -> List[Meeting]:
        """Get all upcoming meetings after a specific date."""
        return await self.db.get_meetings_after_date(after_date)
    
    async def get_meetings_by_organizer(self, organizer_id: int) -> List[Meeting]:
        """Get all meetings organized by a user."""
        return await self.db.get_meetings_by_organizer(organizer_id)
    
    async def get_meetings_by_status(self, status: MeetingStatus) -> List[Meeting]:
        """Get all meetings with a specific status."""
        return await self.db.get_meetings_by_status(status)
    
    async def get_meetings_needing_reminders(
        self, 
        reminder_type: str,  # '24h', '1h', '15m'
        current_time: datetime
    ) -> List[Meeting]:
        """Get meetings that need reminders sent."""
        return await self.db.get_meetings_needing_reminders(reminder_type, current_time)
    
    # ============================================================================
    # ATTENDEE OPERATIONS
    # ============================================================================
    
    async def add_attendee(self, attendee: MeetingAttendee) -> None:
        """Add an attendee to a meeting."""
        await self.db.insert_meeting_attendee(attendee)
    
    async def add_attendees(self, meeting_id: str, user_ids: List[int], invited_at: datetime) -> None:
        """Add multiple attendees to a meeting."""
        for user_id in user_ids:
            attendee = MeetingAttendee(
                id=None,
                meeting_id=meeting_id,
                user_id=user_id,
                status=AttendanceStatus.INVITED,
                invited_at=invited_at,
                responded_at=None
            )
            await self.add_attendee(attendee)
    
    async def update_attendee_status(
        self, 
        meeting_id: str, 
        user_id: int, 
        status: AttendanceStatus,
        responded_at: datetime
    ) -> None:
        """Update attendee RSVP status."""
        await self.db.update_attendee_status(meeting_id, user_id, status, responded_at)
    
    async def get_meeting_attendees(self, meeting_id: str) -> List[MeetingAttendee]:
        """Get all attendees for a meeting."""
        return await self.db.get_meeting_attendees(meeting_id)
    
    async def get_user_meetings(self, user_id: int, after_date: Optional[datetime] = None) -> List[Meeting]:
        """Get all meetings a user is invited to."""
        return await self.db.get_user_meetings(user_id, after_date)
    
    async def get_attendee_status(self, meeting_id: str, user_id: int) -> Optional[AttendanceStatus]:
        """Get attendee's RSVP status for a meeting."""
        attendee = await self.db.get_meeting_attendee(meeting_id, user_id)
        return attendee.status if attendee else None
    
    async def get_non_responders(self, meeting_id: str) -> List[int]:
        """Get list of user IDs who haven't responded to meeting invite."""
        attendees = await self.get_meeting_attendees(meeting_id)
        return [a.user_id for a in attendees if a.status == AttendanceStatus.INVITED]
    
    async def get_confirmed_attendees(self, meeting_id: str) -> List[int]:
        """Get list of user IDs who confirmed attendance."""
        attendees = await self.get_meeting_attendees(meeting_id)
        return [
            a.user_id for a in attendees 
            if a.status in [AttendanceStatus.ATTENDING, AttendanceStatus.ATTENDING_PREPARED]
        ]
    
    # ============================================================================
    # MEETING NOTES OPERATIONS
    # ============================================================================
    
    async def create_meeting_notes(self, notes: MeetingNotes) -> None:
        """Create meeting notes."""
        await self.db.insert_meeting_notes(notes)
    
    async def get_meeting_notes(self, meeting_id: str) -> Optional[MeetingNotes]:
        """Get meeting notes by meeting ID."""
        return await self.db.get_meeting_notes_by_meeting_id(meeting_id)
    
    async def get_meeting_notes_by_message_id(self, message_id: int) -> Optional[MeetingNotes]:
        """Get meeting notes by message ID."""
        return await self.db.get_meeting_notes_by_message_id(message_id)
    
    # ============================================================================
    # REACTION OPERATIONS (RSVP)
    # ============================================================================
    
    async def add_reaction(
        self, 
        meeting_id: str, 
        message_id: int,
        user_id: int, 
        reaction: str,
        timestamp: datetime
    ) -> None:
        """Add a reaction to a meeting invitation."""
        meeting_reaction = MeetingReaction(
            id=None,
            meeting_id=meeting_id,
            message_id=message_id,
            user_id=user_id,
            reaction=reaction,
            timestamp=timestamp
        )
        await self.db.insert_meeting_reaction(meeting_reaction)
    
    async def remove_reaction(
        self, 
        meeting_id: str, 
        user_id: int, 
        reaction: str
    ) -> None:
        """Remove a reaction from a meeting."""
        await self.db.remove_meeting_reaction(meeting_id, user_id, reaction)
    
    async def get_meeting_reactions(self, meeting_id: str) -> List[MeetingReaction]:
        """Get all reactions for a meeting."""
        return await self.db.get_meeting_reactions(meeting_id)
    
    async def get_user_reaction(self, meeting_id: str, user_id: int) -> Optional[str]:
        """Get user's latest reaction for a meeting."""
        reactions = await self.db.get_user_meeting_reactions(meeting_id, user_id)
        if reactions:
            # Return the most recent reaction
            latest = max(reactions, key=lambda r: r.timestamp)
            return latest.reaction
        return None
