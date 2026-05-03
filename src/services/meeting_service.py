"""Meeting service for meeting management business logic."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from src.data.models import (
    Meeting,
    MeetingStatus,
    MeetingPriority,
    MeetingAttendee,
    AttendanceStatus,
    MeetingNotes,
)
from src.data.repositories.meeting_repository import MeetingRepository
from src.data.repositories.user_repository import UserRepository
from src.config import Config

logger = logging.getLogger(__name__)


class MeetingService:
    """Service for meeting management operations."""
    
    def __init__(
        self,
        meeting_repo: MeetingRepository,
        user_repo: UserRepository,
        config: Config
    ):
        """Initialize meeting service."""
        self.meeting_repo = meeting_repo
        self.user_repo = user_repo
        self.config = config
    
    async def generate_meeting_id(self) -> str:
        """
        Generate unique meeting ID in format: MTG-YYMM-XX
        Example: MTG-2605-01, MTG-2605-02, etc.
        """
        now = datetime.now()
        year_month = now.strftime("%y%m")  # e.g., "2605" for May 2026
        
        # Get all meetings from this month
        month_start = datetime(now.year, now.month, 1)
        month_meetings = await self.meeting_repo.get_upcoming_meetings(month_start)
        
        # Filter to only this month
        this_month_meetings = [
            m for m in month_meetings 
            if m.meeting_id.startswith(f"MTG-{year_month}")
        ]
        
        # Find next available number
        if not this_month_meetings:
            sequence = 1
        else:
            # Extract sequence numbers
            sequences = []
            for meeting in this_month_meetings:
                try:
                    seq = int(meeting.meeting_id.split('-')[-1])
                    sequences.append(seq)
                except:
                    pass
            
            sequence = max(sequences) + 1 if sequences else 1
        
        meeting_id = f"MTG-{year_month}-{sequence:02d}"
        logger.info(f"✅ Generated meeting ID: {meeting_id}")
        return meeting_id
    
    async def create_meeting(
        self,
        title: str,
        date: datetime,
        duration_minutes: int,
        location: str,
        organizer_id: int,
        attendee_ids: List[int],
        agenda: str,
        priority: MeetingPriority,
        message_id: int,
        topic_id: int,
        preparation: Optional[str] = None,
        user_provided_id: Optional[str] = None
    ) -> Optional[Meeting]:
        """
        Create a new meeting invitation.
        
        Args:
            title: Meeting title
            date: Meeting date and time
            duration_minutes: Duration in minutes
            location: Location (physical, Zoom link, etc.)
            organizer_id: User ID of organizer
            attendee_ids: List of user IDs to invite
            agenda: Meeting agenda
            priority: Meeting priority
            message_id: Telegram message ID
            topic_id: Telegram topic ID
            preparation: Optional preparation instructions
            user_provided_id: Optional user-provided meeting ID (will be validated/corrected)
        
        Returns:
            Created meeting or None if creation failed
        """
        logger.info(f"🎯 create_meeting called: title={title}, organizer={organizer_id}, attendees={len(attendee_ids)}")
        
        # Validate and generate meeting ID
        meeting_id = None
        
        if user_provided_id:
            # Check if user-provided ID is valid format
            import re
            if re.match(r'^MTG-\d{4}-\d{2}$', user_provided_id):
                # Check if ID already exists
                existing = await self.meeting_repo.get_meeting(user_provided_id)
                if not existing:
                    meeting_id = user_provided_id
                    logger.info(f"✅ Using user-provided meeting ID: {meeting_id}")
                else:
                    logger.warning(f"⚠️ User-provided ID {user_provided_id} already exists, generating new one")
            else:
                logger.warning(f"⚠️ User-provided ID {user_provided_id} has invalid format, generating new one")
        
        # Generate new ID if user-provided ID was invalid or duplicate
        if not meeting_id:
            meeting_id = await self.generate_meeting_id()
        
        # Create meeting
        meeting = Meeting(
            meeting_id=meeting_id,
            title=title,
            date=date,
            duration_minutes=duration_minutes,
            location=location,
            organizer_id=organizer_id,
            agenda=agenda,
            priority=priority,
            status=MeetingStatus.SCHEDULED,
            created_at=datetime.now(),
            message_id=message_id,
            topic_id=topic_id,
            preparation=preparation
        )
        
        try:
            # Save meeting
            await self.meeting_repo.create_meeting(meeting)
            logger.info(f"✅ Created meeting {meeting_id}")
            
            # Add attendees
            await self.meeting_repo.add_attendees(
                meeting_id=meeting_id,
                user_ids=attendee_ids,
                invited_at=datetime.now()
            )
            logger.info(f"✅ Added {len(attendee_ids)} attendees to meeting {meeting_id}")
            
            # Send DM notifications to attendees
            await self._send_meeting_invitations(meeting, attendee_ids)
            
            return meeting
            
        except Exception as e:
            logger.error(f"❌ Failed to create meeting: {e}", exc_info=True)
            return None
    
    async def process_rsvp_reaction(
        self,
        meeting_id: str,
        reaction: str,
        user_id: int,
        message_id: int
    ) -> bool:
        """
        Process RSVP reaction on meeting invitation.
        
        Reaction mapping:
        - 👍 = ATTENDING
        - ❤️ = ATTENDING_PREPARED
        - 👎 = CANNOT_ATTEND
        - 🔥 = URGENT_CONFLICT
        
        Args:
            meeting_id: Meeting ID
            reaction: Reaction emoji
            user_id: User who reacted
            message_id: Message ID
        
        Returns:
            True if processed successfully
        """
        logger.info(f"🎯 process_rsvp_reaction: meeting={meeting_id}, reaction={reaction}, user={user_id}")
        
        # Map reaction to attendance status
        reaction_map = {
            '👍': AttendanceStatus.ATTENDING,
            '❤️': AttendanceStatus.ATTENDING_PREPARED,
            '👎': AttendanceStatus.CANNOT_ATTEND,
            '🔥': AttendanceStatus.URGENT_CONFLICT
        }
        
        status = reaction_map.get(reaction)
        if not status:
            logger.warning(f"⚠️ Unknown reaction for meeting RSVP: {reaction}")
            return False
        
        try:
            # Get meeting
            meeting = await self.meeting_repo.get_meeting(meeting_id)
            if not meeting:
                logger.error(f"❌ Meeting not found: {meeting_id}")
                return False
            
            # Update attendee status
            await self.meeting_repo.update_attendee_status(
                meeting_id=meeting_id,
                user_id=user_id,
                status=status,
                responded_at=datetime.now()
            )
            
            # Record reaction
            await self.meeting_repo.add_reaction(
                meeting_id=meeting_id,
                message_id=message_id,
                user_id=user_id,
                reaction=reaction,
                timestamp=datetime.now()
            )
            
            logger.info(f"✅ Updated RSVP for user {user_id} to {status.value}")
            
            # Send confirmation DM
            await self._send_rsvp_confirmation(meeting, user_id, status)
            
            # Alert organizer if urgent conflict
            if status == AttendanceStatus.URGENT_CONFLICT:
                await self._alert_organizer_urgent_conflict(meeting, user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process RSVP: {e}", exc_info=True)
            return False
    
    async def post_meeting_notes(
        self,
        meeting_id: str,
        posted_by: int,
        message_id: int,
        attendees_present: str,
        decisions: str,
        action_items: str,
        next_meeting_date: Optional[datetime] = None
    ) -> Optional[MeetingNotes]:
        """
        Post meeting notes after meeting completion.
        
        Args:
            meeting_id: Meeting ID
            posted_by: User ID who posted notes
            message_id: Telegram message ID of notes
            attendees_present: Comma-separated attendees who attended
            decisions: Decisions made
            action_items: Action items assigned
            next_meeting_date: Optional next meeting date
        
        Returns:
            Created meeting notes or None if failed
        """
        logger.info(f"🎯 post_meeting_notes: meeting={meeting_id}, posted_by={posted_by}")
        
        try:
            # Create notes
            notes = MeetingNotes(
                id=None,
                meeting_id=meeting_id,
                posted_by=posted_by,
                posted_at=datetime.now(),
                message_id=message_id,
                attendees_present=attendees_present,
                decisions=decisions,
                action_items=action_items,
                next_meeting_date=next_meeting_date
            )
            
            # Save notes
            await self.meeting_repo.create_meeting_notes(notes)
            
            # Link notes to meeting
            await self.meeting_repo.link_meeting_notes(meeting_id, message_id)
            
            # Update meeting status to COMPLETED
            await self.meeting_repo.update_meeting_status(
                meeting_id=meeting_id,
                status=MeetingStatus.COMPLETED,
                timestamp=datetime.now()
            )
            
            logger.info(f"✅ Posted meeting notes for {meeting_id}")
            
            # Send notifications to attendees
            await self._send_notes_notifications(meeting_id, message_id)
            
            return notes
            
        except Exception as e:
            logger.error(f"❌ Failed to post meeting notes: {e}", exc_info=True)
            return None
    
    async def cancel_meeting(
        self,
        meeting_id: str,
        cancelled_by: int,
        reason: str
    ) -> bool:
        """
        Cancel a meeting.
        
        Args:
            meeting_id: Meeting ID
            cancelled_by: User ID who cancelled
            reason: Cancellation reason
        
        Returns:
            True if cancelled successfully
        """
        logger.info(f"🎯 cancel_meeting: meeting={meeting_id}, cancelled_by={cancelled_by}")
        
        try:
            # Get meeting
            meeting = await self.meeting_repo.get_meeting(meeting_id)
            if not meeting:
                logger.error(f"❌ Meeting not found: {meeting_id}")
                return False
            
            # Cancel meeting
            await self.meeting_repo.cancel_meeting(
                meeting_id=meeting_id,
                reason=reason,
                cancelled_at=datetime.now()
            )
            
            logger.info(f"✅ Cancelled meeting {meeting_id}")
            
            # Notify attendees
            await self._send_cancellation_notifications(meeting, reason)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel meeting: {e}", exc_info=True)
            return False
    
    async def get_user_upcoming_meetings(self, user_id: int) -> List[Meeting]:
        """Get user's upcoming meetings."""
        now = datetime.now()
        meetings = await self.meeting_repo.get_user_meetings(user_id, after_date=now)
        
        # Filter to only scheduled meetings
        return [m for m in meetings if m.status == MeetingStatus.SCHEDULED]
    
    async def get_meeting_by_message_id(self, message_id: int) -> Optional[Meeting]:
        """Get meeting by Telegram message ID."""
        return await self.meeting_repo.get_meeting_by_message_id(message_id)
    
    async def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get meeting by ID."""
        return await self.meeting_repo.get_meeting(meeting_id)
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    async def _send_meeting_invitations(self, meeting: Meeting, attendee_ids: List[int]):
        """Send DM invitations to all attendees."""
        try:
            from telegram import Bot
            from src.utils.link_builder import build_message_link
            
            bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            
            # Get organizer username
            organizer = await self.user_repo.get_user(meeting.organizer_id)
            organizer_username = organizer.username if organizer and organizer.username else f"User {meeting.organizer_id}"
            
            # Build link to meeting message
            meeting_link = build_message_link(self.config.TELEGRAM_GROUP_ID, meeting.message_id)
            
            # Format date and time
            date_str = meeting.date.strftime("%Y-%m-%d")
            time_str = meeting.date.strftime("%H:%M")
            
            # Priority emoji
            priority_emoji = {
                MeetingPriority.LOW: "🟢",
                MeetingPriority.MEDIUM: "🟡",
                MeetingPriority.HIGH: "🟠",
                MeetingPriority.URGENT: "🔴"
            }.get(meeting.priority, "📋")
            
            message_text = f"""{priority_emoji} **Meeting Invitation**

**Title:** {meeting.title}
**Date:** {date_str}
**Time:** {time_str}
**Duration:** {meeting.duration_minutes} minutes
**Location:** {meeting.location}
**Organizer:** @{organizer_username}

[📎 View Full Invitation]({meeting_link})

**Please RSVP:**
👍 = I will attend
❤️ = I will attend (prepared)
👎 = Cannot attend
🔥 = Urgent conflict (need reschedule)

_⏱️ This message will auto-delete in 180 seconds_"""
            
            # Send to each attendee
            for attendee_id in attendee_ids:
                try:
                    await bot.send_message(
                        chat_id=attendee_id,
                        text=message_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    logger.info(f"✅ Sent meeting invitation DM to user {attendee_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send invitation to user {attendee_id}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send meeting invitations: {e}", exc_info=True)
    
    async def _send_rsvp_confirmation(self, meeting: Meeting, user_id: int, status: AttendanceStatus):
        """Send RSVP confirmation DM to user."""
        try:
            from telegram import Bot
            
            bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            
            status_messages = {
                AttendanceStatus.ATTENDING: "✅ You confirmed attendance",
                AttendanceStatus.ATTENDING_PREPARED: "✅ You confirmed attendance (prepared)",
                AttendanceStatus.CANNOT_ATTEND: "❌ You declined attendance",
                AttendanceStatus.URGENT_CONFLICT: "🔥 You reported urgent conflict"
            }
            
            message = status_messages.get(status, "✅ RSVP recorded")
            
            message_text = f"""**RSVP Confirmed**

{message} for:
**{meeting.title}**
**Date:** {meeting.date.strftime("%Y-%m-%d %H:%M")}

_⏱️ This message will auto-delete in 30 seconds_"""
            
            await bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='Markdown'
            )
            logger.info(f"✅ Sent RSVP confirmation to user {user_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to send RSVP confirmation: {e}")
    
    async def _alert_organizer_urgent_conflict(self, meeting: Meeting, user_id: int):
        """Alert organizer about urgent conflict."""
        try:
            from telegram import Bot
            
            bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            
            # Get user info
            user = await self.user_repo.get_user(user_id)
            username = user.username if user and user.username else f"User {user_id}"
            
            message_text = f"""🔥 **Urgent Meeting Conflict**

@{username} reported an urgent conflict for:
**{meeting.title}**
**Date:** {meeting.date.strftime("%Y-%m-%d %H:%M")}

Consider rescheduling or contacting the attendee.

_⏱️ This message will auto-delete in 120 seconds_"""
            
            await bot.send_message(
                chat_id=meeting.organizer_id,
                text=message_text,
                parse_mode='Markdown'
            )
            logger.info(f"✅ Alerted organizer {meeting.organizer_id} about urgent conflict")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to alert organizer: {e}")
    
    async def _send_notes_notifications(self, meeting_id: str, notes_message_id: int):
        """Send notifications about posted meeting notes."""
        try:
            from telegram import Bot
            from src.utils.link_builder import build_message_link
            
            bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            
            # Get meeting and attendees
            meeting = await self.meeting_repo.get_meeting(meeting_id)
            if not meeting:
                return
            
            attendees = await self.meeting_repo.get_meeting_attendees(meeting_id)
            
            # Build link to notes
            notes_link = build_message_link(self.config.TELEGRAM_GROUP_ID, notes_message_id)
            
            message_text = f"""📝 **Meeting Notes Posted**

Notes have been posted for:
**{meeting.title}**
**Date:** {meeting.date.strftime("%Y-%m-%d")}

[📎 View Meeting Notes]({notes_link})

_⏱️ This message will auto-delete in 120 seconds_"""
            
            # Send to all attendees
            for attendee in attendees:
                try:
                    await bot.send_message(
                        chat_id=attendee.user_id,
                        text=message_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send notes notification to user {attendee.user_id}: {e}")
            
            logger.info(f"✅ Sent notes notifications for meeting {meeting_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send notes notifications: {e}", exc_info=True)
    
    async def _send_cancellation_notifications(self, meeting: Meeting, reason: str):
        """Send cancellation notifications to attendees."""
        try:
            from telegram import Bot
            
            bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            
            # Get attendees
            attendees = await self.meeting_repo.get_meeting_attendees(meeting.meeting_id)
            
            message_text = f"""❌ **Meeting Cancelled**

The following meeting has been cancelled:
**{meeting.title}**
**Date:** {meeting.date.strftime("%Y-%m-%d %H:%M")}

**Reason:** {reason}

_⏱️ This message will auto-delete in 120 seconds_"""
            
            # Send to all attendees
            for attendee in attendees:
                try:
                    await bot.send_message(
                        chat_id=attendee.user_id,
                        text=message_text,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send cancellation to user {attendee.user_id}: {e}")
            
            logger.info(f"✅ Sent cancellation notifications for meeting {meeting.meeting_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send cancellation notifications: {e}", exc_info=True)
