"""Meeting reminder service for sending automated reminders before meetings."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from src.data.models import Meeting, MeetingStatus
from src.data.repositories.meeting_repository import MeetingRepository
from src.data.repositories.user_repository import UserRepository
from src.config import Config

logger = logging.getLogger(__name__)


class MeetingReminderService:
    """Service for sending automated meeting reminders."""
    
    def __init__(
        self,
        meeting_repo: MeetingRepository,
        user_repo: UserRepository,
        bot_context,
        config: Config
    ):
        """Initialize meeting reminder service."""
        self.meeting_repo = meeting_repo
        self.user_repo = user_repo
        self.bot_context = bot_context
        self.config = config
        self.bot = bot_context.bot
        self._task = None
        self._running = False
    
    async def start(self):
        """Start the meeting reminder service."""
        if self._running:
            logger.warning("Meeting reminder service already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("✅ Meeting reminder service started")
    
    async def stop(self):
        """Stop the meeting reminder service."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Meeting reminder service stopped")
    
    async def _run_loop(self):
        """Main service loop - checks every 5 minutes."""
        logger.info("Meeting reminder service loop started")
        
        while self._running:
            try:
                await self.check_and_send_reminders()
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                logger.info("Meeting reminder service loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in meeting reminder service loop: {e}", exc_info=True)
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def check_and_send_reminders(self):
        """
        Check for meetings needing reminders and send them.
        Should be called periodically (every 5 minutes recommended).
        """
        try:
            current_time = datetime.now()
            
            # Check for 24-hour reminders
            await self._send_reminders_24h(current_time)
            
            # Check for 1-hour reminders
            await self._send_reminders_1h(current_time)
            
            # Check for 15-minute reminders
            await self._send_reminders_15m(current_time)
            
        except Exception as e:
            logger.error(f"❌ Error checking meeting reminders: {e}", exc_info=True)
    
    async def _send_reminders_24h(self, current_time: datetime):
        """Send 24-hour reminders."""
        try:
            meetings = await self.meeting_repo.get_meetings_needing_reminders('24h', current_time)
            
            if not meetings:
                return
            
            logger.info(f"📅 Found {len(meetings)} meetings needing 24-hour reminders")
            
            for meeting in meetings:
                await self._send_reminder_to_attendees(
                    meeting=meeting,
                    reminder_type='24h',
                    time_until="24 hours"
                )
                
                # Mark reminder as sent
                await self.meeting_repo.update_meeting_reminder(
                    meeting_id=meeting.meeting_id,
                    reminder_type='24h',
                    timestamp=current_time
                )
                
                logger.info(f"✅ Sent 24-hour reminder for meeting {meeting.meeting_id}")
        
        except Exception as e:
            logger.error(f"❌ Error sending 24-hour reminders: {e}", exc_info=True)
    
    async def _send_reminders_1h(self, current_time: datetime):
        """Send 1-hour reminders."""
        try:
            meetings = await self.meeting_repo.get_meetings_needing_reminders('1h', current_time)
            
            if not meetings:
                return
            
            logger.info(f"📅 Found {len(meetings)} meetings needing 1-hour reminders")
            
            for meeting in meetings:
                await self._send_reminder_to_attendees(
                    meeting=meeting,
                    reminder_type='1h',
                    time_until="1 hour"
                )
                
                # Mark reminder as sent
                await self.meeting_repo.update_meeting_reminder(
                    meeting_id=meeting.meeting_id,
                    reminder_type='1h',
                    timestamp=current_time
                )
                
                logger.info(f"✅ Sent 1-hour reminder for meeting {meeting.meeting_id}")
        
        except Exception as e:
            logger.error(f"❌ Error sending 1-hour reminders: {e}", exc_info=True)
    
    async def _send_reminders_15m(self, current_time: datetime):
        """Send 15-minute reminders."""
        try:
            meetings = await self.meeting_repo.get_meetings_needing_reminders('15m', current_time)
            
            if not meetings:
                return
            
            logger.info(f"📅 Found {len(meetings)} meetings needing 15-minute reminders")
            
            for meeting in meetings:
                await self._send_reminder_to_attendees(
                    meeting=meeting,
                    reminder_type='15m',
                    time_until="15 minutes"
                )
                
                # Mark reminder as sent
                await self.meeting_repo.update_meeting_reminder(
                    meeting_id=meeting.meeting_id,
                    reminder_type='15m',
                    timestamp=current_time
                )
                
                logger.info(f"✅ Sent 15-minute reminder for meeting {meeting.meeting_id}")
        
        except Exception as e:
            logger.error(f"❌ Error sending 15-minute reminders: {e}", exc_info=True)
    
    async def _send_reminder_to_attendees(
        self, 
        meeting: Meeting, 
        reminder_type: str,
        time_until: str
    ):
        """Send reminder DM to all attendees."""
        try:
            # Get all attendees
            attendees = await self.meeting_repo.get_meeting_attendees(meeting.meeting_id)
            
            if not attendees:
                logger.warning(f"⚠️ No attendees found for meeting {meeting.meeting_id}")
                return
            
            # Get organizer info
            organizer = await self.user_repo.get_user(meeting.organizer_id)
            organizer_name = f"@{organizer.username}" if organizer and organizer.username else f"User {meeting.organizer_id}"
            
            # Build message link
            from src.utils.link_builder import build_message_link
            meeting_link = build_message_link(self.config.TELEGRAM_GROUP_ID, meeting.message_id)
            
            # Format date and time
            date_str = meeting.date.strftime("%Y-%m-%d")
            time_str = meeting.date.strftime("%H:%M")
            
            # Priority emoji
            priority_emoji = {
                "LOW": "🟢",
                "MEDIUM": "🟡",
                "HIGH": "🟠",
                "URGENT": "🔴"
            }.get(meeting.priority.value, "📋")
            
            # Reminder emoji based on urgency
            reminder_emoji = {
                '24h': "📅",
                '1h': "⏰",
                '15m': "🔔"
            }.get(reminder_type, "⏰")
            
            # Build reminder message
            message_text = f"""{reminder_emoji} **Meeting Reminder - {time_until}**

{priority_emoji} **{meeting.title}**

**Meeting ID:** #{meeting.meeting_id}
**Date:** {date_str}
**Time:** {time_str}
**Duration:** {meeting.duration_minutes} minutes
**Location:** {meeting.location}
**Organizer:** {organizer_name}

[📎 View Full Details]({meeting_link})

"""
            
            # Add preparation reminder if exists
            if meeting.preparation:
                message_text += f"**⚠️ Preparation Required:**\n{meeting.preparation}\n\n"
            
            # Add agenda
            if meeting.agenda:
                # Truncate agenda if too long
                agenda_preview = meeting.agenda[:200] + "..." if len(meeting.agenda) > 200 else meeting.agenda
                message_text += f"**Agenda:**\n{agenda_preview}\n\n"
            
            message_text += "_This is an automated reminder_"
            
            # Send to each attendee
            sent_count = 0
            failed_count = 0
            
            for attendee in attendees:
                try:
                    # Get attendee RSVP status
                    status_emoji = {
                        "INVITED": "❓ (Please RSVP)",
                        "ATTENDING": "✅ (You confirmed)",
                        "ATTENDING_PREPARED": "❤️ (You're prepared)",
                        "CANNOT_ATTEND": "❌ (You declined)",
                        "URGENT_CONFLICT": "🔥 (You reported conflict)"
                    }.get(attendee.status.value, "❓")
                    
                    # Add RSVP status to message
                    attendee_message = message_text + f"\n\n**Your RSVP:** {status_emoji}"
                    
                    # Send DM
                    await self.bot.send_message(
                        chat_id=attendee.user_id,
                        text=attendee_message,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    
                    sent_count += 1
                    logger.info(f"✅ Sent {reminder_type} reminder to user {attendee.user_id} for meeting {meeting.meeting_id}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"⚠️ Failed to send reminder to user {attendee.user_id}: {e}")
            
            logger.info(f"📊 Reminder summary for {meeting.meeting_id}: {sent_count} sent, {failed_count} failed")
            
            # Also send reminder to organizer
            try:
                organizer_message = f"""{reminder_emoji} **Meeting Reminder - {time_until}** (Organizer)

{priority_emoji} **{meeting.title}**

**Meeting ID:** #{meeting.meeting_id}
**Date:** {date_str}
**Time:** {time_str}
**Duration:** {meeting.duration_minutes} minutes

[📎 View Meeting]({meeting_link})

**Attendees:** {len(attendees)} invited
**Confirmed:** {len([a for a in attendees if a.status.value in ['ATTENDING', 'ATTENDING_PREPARED']])}
**Pending:** {len([a for a in attendees if a.status.value == 'INVITED'])}
**Declined:** {len([a for a in attendees if a.status.value == 'CANNOT_ATTEND'])}

_This is an automated reminder for the organizer_"""
                
                await self.bot.send_message(
                    chat_id=meeting.organizer_id,
                    text=organizer_message,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                
                logger.info(f"✅ Sent {reminder_type} reminder to organizer {meeting.organizer_id}")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to send reminder to organizer: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error sending reminder to attendees: {e}", exc_info=True)
