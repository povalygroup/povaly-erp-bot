"""Birthday Service - Handles birthday wishes and reminders."""

import logging
from typing import List, Optional
from datetime import datetime, date

from src.data.models.user import User

logger = logging.getLogger(__name__)


class BirthdayService:
    """Service for managing birthday wishes and reminders."""
    
    def __init__(self, user_repo, config):
        """Initialize birthday service."""
        self.user_repo = user_repo
        self.config = config
    
    async def check_and_send_birthday_wishes(self, context) -> int:
        """
        Check for birthdays today and send automatic wishes.
        
        Returns:
            Number of wishes sent
        """
        try:
            # Get users with birthday today
            birthday_users = await self.user_repo.get_users_with_birthday_today()
            
            if not birthday_users:
                logger.info("No birthdays today")
                return 0
            
            logger.info(f"Found {len(birthday_users)} birthday(s) today")
            
            wishes_sent = 0
            today_str = date.today().isoformat()
            
            for user in birthday_users:
                # Check if custom message already sent today
                if user.custom_birthday_message and user.birthday_wishes_sent == today_str:
                    logger.info(f"Custom wish already sent for user {user.user_id}, skipping auto wish")
                    continue
                
                # Check if auto wish already sent today
                if user.birthday_wishes_sent == today_str:
                    logger.info(f"Auto wish already sent for user {user.user_id} today")
                    continue
                
                # Send auto birthday wish
                success = await self.send_auto_birthday_wish(context, user)
                if success:
                    wishes_sent += 1
            
            logger.info(f"Sent {wishes_sent} birthday wishes")
            return wishes_sent
            
        except Exception as e:
            logger.error(f"Error checking and sending birthday wishes: {e}")
            return 0
    
    async def send_auto_birthday_wish(self, context, user: User) -> bool:
        """
        Send automatic birthday wish to user.
        
        Sends:
        - DM to user (if enabled)
        - Announcement to Official Directives (if enabled)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            dm_sent = False
            group_sent = False
            
            # Send DM to user
            if self.config.BIRTHDAY_SEND_DM:
                dm_message = self.format_birthday_dm(user)
                try:
                    await context.bot.send_message(
                        chat_id=user.user_id,
                        text=dm_message,
                        parse_mode=None
                    )
                    dm_sent = True
                    logger.info(f"Sent birthday DM to user {user.user_id}")
                except Exception as e:
                    logger.error(f"Failed to send birthday DM to user {user.user_id}: {e}")
            
            # Send announcement to Official Directives
            if self.config.BIRTHDAY_SEND_GROUP and self.config.TOPIC_OFFICIAL_DIRECTIVES:
                group_message = self.format_birthday_announcement(user)
                try:
                    await context.bot.send_message(
                        chat_id=self.config.TELEGRAM_GROUP_ID,
                        text=group_message,
                        message_thread_id=self.config.TOPIC_OFFICIAL_DIRECTIVES,
                        parse_mode=None
                    )
                    group_sent = True
                    logger.info(f"Sent birthday announcement for user {user.user_id}")
                except Exception as e:
                    logger.error(f"Failed to send birthday announcement for user {user.user_id}: {e}")
            
            # Mark as sent and log
            if dm_sent or group_sent:
                today_str = date.today().isoformat()
                await self.user_repo.mark_birthday_wishes_sent(user.user_id, today_str)
                await self.user_repo.log_birthday_wish(
                    user.user_id, today_str, "auto",
                    None, None, dm_sent, group_sent
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending auto birthday wish for user {user.user_id}: {e}")
            return False
    
    async def send_custom_birthday_wish(self, context, user: User, custom_message: str, admin_user: User) -> bool:
        """
        Send custom birthday wish from admin.
        
        Sends:
        - Custom DM to user
        - Custom announcement to Official Directives
        
        Returns:
            True if successful, False otherwise
        """
        try:
            dm_sent = False
            group_sent = False
            
            # Send custom DM to user
            dm_message = self.format_custom_birthday_dm(user, custom_message, admin_user)
            try:
                await context.bot.send_message(
                    chat_id=user.user_id,
                    text=dm_message,
                    parse_mode=None
                )
                dm_sent = True
                logger.info(f"Sent custom birthday DM to user {user.user_id}")
            except Exception as e:
                logger.error(f"Failed to send custom birthday DM to user {user.user_id}: {e}")
            
            # Send custom announcement to Official Directives
            if self.config.TOPIC_OFFICIAL_DIRECTIVES:
                group_message = self.format_custom_birthday_announcement(user, custom_message, admin_user)
                try:
                    await context.bot.send_message(
                        chat_id=self.config.TELEGRAM_GROUP_ID,
                        text=group_message,
                        message_thread_id=self.config.TOPIC_OFFICIAL_DIRECTIVES,
                        parse_mode=None
                    )
                    group_sent = True
                    logger.info(f"Sent custom birthday announcement for user {user.user_id}")
                except Exception as e:
                    logger.error(f"Failed to send custom birthday announcement for user {user.user_id}: {e}")
            
            # Mark as sent and log
            if dm_sent or group_sent:
                today_str = date.today().isoformat()
                await self.user_repo.mark_birthday_wishes_sent(user.user_id, today_str)
                await self.user_repo.set_custom_birthday_message(user.user_id, custom_message)
                await self.user_repo.log_birthday_wish(
                    user.user_id, today_str, "custom",
                    custom_message, admin_user.user_id, dm_sent, group_sent
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending custom birthday wish for user {user.user_id}: {e}")
            return False
    
    async def send_birthday_reminders(self, context) -> int:
        """
        Send birthday reminders for tomorrow's birthdays.
        
        Sends reminders to:
        - Birthday users (if enabled)
        - Admin DM receivers (if enabled)
        - Admin Control Panel (if enabled)
        
        Returns:
            Number of reminders sent
        """
        try:
            # Get users with birthday tomorrow
            birthday_users = await self.user_repo.get_users_with_birthday_tomorrow()
            
            if not birthday_users:
                logger.info("No birthdays tomorrow")
                return 0
            
            logger.info(f"Found {len(birthday_users)} birthday(s) tomorrow")
            
            reminders_sent = 0
            today_str = date.today().isoformat()
            
            # Send reminder to each birthday user
            if self.config.BIRTHDAY_REMINDER_SEND_TO_USER:
                for user in birthday_users:
                    # Check if reminder already sent today
                    if user.birthday_reminder_sent == today_str:
                        logger.info(f"Reminder already sent for user {user.user_id} today")
                        continue
                    
                    success = await self.send_reminder_to_user(context, user)
                    if success:
                        reminders_sent += 1
            
            # Send consolidated reminder to admin DM receivers
            if self.config.BIRTHDAY_REMINDER_SEND_TO_ADMIN_DM and hasattr(self.config, 'ADMIN_DM_RECIPIENTS'):
                if self.config.ADMIN_DM_RECIPIENTS:
                    success = await self.send_reminder_to_admin_dm(context, birthday_users)
                    if success:
                        reminders_sent += 1
            
            # Send consolidated reminder to Admin Control Panel
            if self.config.BIRTHDAY_REMINDER_SEND_TO_ADMIN_PANEL and self.config.TOPIC_ADMIN_CONTROL_PANEL:
                success = await self.send_reminder_to_admin_panel(context, birthday_users)
                if success:
                    reminders_sent += 1
            
            # Mark reminders as sent
            for user in birthday_users:
                await self.user_repo.mark_birthday_reminder_sent(user.user_id, today_str)
                
                tomorrow_str = (date.today().replace(day=date.today().day + 1)).isoformat()
                await self.user_repo.log_birthday_reminder(
                    user.user_id, today_str, tomorrow_str,
                    self.config.BIRTHDAY_REMINDER_SEND_TO_USER,
                    self.config.BIRTHDAY_REMINDER_SEND_TO_ADMIN_DM,
                    self.config.BIRTHDAY_REMINDER_SEND_TO_ADMIN_PANEL
                )
            
            logger.info(f"Sent {reminders_sent} birthday reminders")
            return reminders_sent
            
        except Exception as e:
            logger.error(f"Error sending birthday reminders: {e}")
            return 0
    
    async def send_reminder_to_user(self, context, user: User) -> bool:
        """Send birthday reminder DM to user."""
        try:
            message = self.format_reminder_to_user(user)
            await context.bot.send_message(
                chat_id=user.user_id,
                text=message,
                parse_mode=None
            )
            logger.info(f"Sent birthday reminder to user {user.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send birthday reminder to user {user.user_id}: {e}")
            return False
    
    async def send_reminder_to_admin_dm(self, context, users: List[User]) -> bool:
        """Send consolidated birthday reminder to admin DM receivers."""
        try:
            message = self.format_reminder_to_admin_dm(users)
            
            sent_count = 0
            for admin_id in self.config.ADMIN_DM_RECIPIENTS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode=None
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send birthday reminder to admin {admin_id}: {e}")
            
            if sent_count > 0:
                logger.info(f"Sent birthday reminder to {sent_count} admin(s)")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error sending birthday reminder to admin DM: {e}")
            return False
    
    async def send_reminder_to_admin_panel(self, context, users: List[User]) -> bool:
        """Send consolidated birthday reminder to Admin Control Panel."""
        try:
            message = self.format_reminder_to_admin_panel(users)
            await context.bot.send_message(
                chat_id=self.config.TELEGRAM_GROUP_ID,
                text=message,
                message_thread_id=self.config.TOPIC_ADMIN_CONTROL_PANEL,
                parse_mode=None
            )
            logger.info("Sent birthday reminder to Admin Control Panel")
            return True
        except Exception as e:
            logger.error(f"Failed to send birthday reminder to Admin Control Panel: {e}")
            return False
    
    # Formatting methods
    
    def format_birthday_dm(self, user: User, custom_message: Optional[str] = None) -> str:
        """Format birthday DM message."""
        display_name = user.get_display_name()
        
        message = f"""🎉🎂 HAPPY BIRTHDAY, {display_name}! 🎂🎉

Wishing you a fantastic birthday filled with joy, success, and wonderful moments! 🌟

May this special day bring you happiness and may the year ahead be filled with great achievements and prosperity! 🎊
"""
        
        # Add age if available and configured
        if self.config.BIRTHDAY_INCLUDE_AGE:
            age = user.get_age()
            if age:
                message += f"\nYou're turning {age} today! 🎈\n"
        
        message += """
Thank you for being an amazing part of our team! 💙

Enjoy your special day! 🥳

With warm wishes,
The Pova Team 🎈"""
        
        # Add employee info if available
        if user.position or user.department or user.join_date:
            message += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nYour Profile:"
            if user.position:
                message += f"\n💼 Position: {user.position}"
            if user.department:
                message += f"\n🏢 Department: {user.department}"
            if user.join_date:
                message += f"\n📅 With us since: {user.join_date}"
            message += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return message
    
    def format_birthday_announcement(self, user: User) -> str:
        """Format birthday announcement for Official Directives."""
        display_name = user.get_display_name()
        username = f"@{user.username}" if user.username else ""
        
        message = f"""🎉🎂 BIRTHDAY CELEBRATION 🎂🎉

Today is a special day! Let's all wish a very Happy Birthday to:

👤 {display_name} {username}"""
        
        if user.position or user.department:
            if user.position and user.department:
                message += f"\n💼 {user.position} | 🏢 {user.department}"
            elif user.position:
                message += f"\n💼 {user.position}"
            elif user.department:
                message += f"\n🏢 {user.department}"
        
        # Add age if configured
        if self.config.BIRTHDAY_INCLUDE_AGE:
            age = user.get_age()
            if age:
                message += f"\n🎈 Turning {age} today!"
        
        message += """

🎊 Join us in celebrating their special day!

Drop your wishes below! 👇
🎈🎁🥳🎉"""
        
        if user.join_date:
            message += f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📅 With Povaly since: {user.join_date}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return message
    
    def format_custom_birthday_dm(self, user: User, custom_message: str, admin_user: User) -> str:
        """Format custom birthday DM."""
        display_name = user.get_display_name()
        admin_name = admin_user.get_display_name()
        
        message = f"""🎉🎂 SPECIAL BIRTHDAY MESSAGE 🎂🎉

Dear {display_name},

{custom_message}

🎈🎁🎊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sent with love by: {admin_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        return message
    
    def format_custom_birthday_announcement(self, user: User, custom_message: str, admin_user: User) -> str:
        """Format custom birthday announcement."""
        display_name = user.get_display_name()
        username = f"@{user.username}" if user.username else ""
        admin_name = admin_user.get_display_name()
        
        message = f"""🎉🎂 SPECIAL BIRTHDAY MESSAGE 🎂🎉

Happy Birthday to: {display_name} {username}

{custom_message}

🎈🎁🎊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sent with love by: {admin_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        return message
    
    def format_reminder_to_user(self, user: User) -> str:
        """Format birthday reminder for user."""
        display_name = user.get_display_name()
        birthday_display = user.get_birthday_display()
        
        message = f"""🎂 Birthday Reminder

Hi {display_name}! 👋

Just a friendly reminder that tomorrow is your birthday! 🎉

📅 Date: {birthday_display}
🎈 We'll be celebrating your special day!

Get ready for some birthday wishes! 🥳

Have a wonderful day! ✨"""
        
        return message
    
    def format_reminder_to_admin_dm(self, users: List[User]) -> str:
        """Format consolidated birthday reminder for admin DM."""
        message = "🎂 Birthday Reminder - Tomorrow\n\n"
        message += f"The following team member{'s' if len(users) > 1 else ''} {'have' if len(users) > 1 else 'has'} birthday{'s' if len(users) > 1 else ''} tomorrow:\n\n"
        
        for idx, user in enumerate(users, 1):
            display_name = user.get_display_name()
            username = f"@{user.username}" if user.username else ""
            birthday_display = user.get_birthday_display()
            
            message += f"{idx}️⃣ {display_name} {username}\n"
            if user.position:
                message += f"   💼 {user.position}"
            if user.department:
                message += f" | 🏢 {user.department}"
            if user.position or user.department:
                message += "\n"
            message += f"   📅 Birthday: {birthday_display}\n"
            
            if self.config.BIRTHDAY_INCLUDE_AGE:
                age = user.get_age()
                if age:
                    message += f"   🎈 Turning {age}\n"
            message += "\n"
        
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"📋 Total: {len(users)} birthday{'s' if len(users) > 1 else ''} tomorrow\n"
        message += "🎉 Automatic wishes will be sent at 9:00 AM\n\n"
        message += "You can send custom wishes with:\n"
        message += "/birthday @username Your custom message\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return message
    
    def format_reminder_to_admin_panel(self, users: List[User]) -> str:
        """Format consolidated birthday reminder for Admin Control Panel."""
        from datetime import timedelta
        tomorrow = date.today() + timedelta(days=1)
        
        message = "🎂 BIRTHDAY REMINDER - TOMORROW\n\n"
        message += f"📅 Date: {tomorrow.strftime('%B %d, %Y')}\n\n"
        message += f"Team member{'s' if len(users) > 1 else ''} with birthday{'s' if len(users) > 1 else ''} tomorrow:\n\n"
        
        for idx, user in enumerate(users, 1):
            display_name = user.get_display_name()
            username = f"@{user.username}" if user.username else ""
            
            message += f"{idx}️⃣ {username} - {display_name}\n"
            if user.position:
                message += f"   💼 {user.position}"
            if user.department:
                message += f" | 🏢 {user.department}"
            if user.position or user.department:
                message += "\n"
            
            if self.config.BIRTHDAY_INCLUDE_AGE:
                age = user.get_age()
                if age:
                    message += f"   🎈 Age: {age}\n"
            message += "\n"
        
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"📋 Total: {len(users)} birthday{'s' if len(users) > 1 else ''}\n"
        message += "⏰ Auto wishes: 9:00 AM tomorrow\n"
        message += "📢 Announcement: Official Directives\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += "Custom wishes: /birthday @username Message"
        
        return message
