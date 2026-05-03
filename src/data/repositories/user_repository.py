"""User repository for data access."""

from typing import Optional, List
from datetime import datetime

from src.data.models import User, UserRole


class UserRepository:
    """Repository for user-related data operations."""
    
    def __init__(self, db):
        """Initialize with database adapter."""
        self.db = db
    
    async def create_user(self, user: User) -> None:
        """Create a new user."""
        await self.db.insert_user(user)
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await self.db.get_user_by_id(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return await self.db.get_user_by_username(username)
    
    async def update_user(self, user: User) -> None:
        """Update user information."""
        await self.db.update_user(user)
    
    async def update_last_active(self, user_id: int, timestamp: datetime) -> None:
        """Update user's last active timestamp."""
        await self.db.update_user_last_active(user_id, timestamp)
    
    async def set_on_leave(self, user_id: int, start_date: datetime, end_date: datetime) -> None:
        """Mark user as on leave."""
        await self.db.set_user_on_leave(user_id, start_date, end_date)
    
    async def clear_leave(self, user_id: int) -> None:
        """Clear user's leave status."""
        await self.db.clear_user_leave(user_id)
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get all users with a specific role."""
        return await self.db.get_users_by_role(role)
    
    async def get_all_users(self) -> List[User]:
        """Get all users."""
        return await self.db.get_all_users()
    
    async def user_exists(self, user_id: int) -> bool:
        """Check if user exists."""
        user = await self.get_user(user_id)
        return user is not None
    
    # Employee Information Methods
    
    async def update_employee_info(self, user_id: int, info_dict: dict, set_by: str = "self") -> None:
        """Update employee information for a user."""
        await self.db.update_employee_info(user_id, info_dict, set_by)
    
    async def get_employee_info(self, user_id: int) -> Optional[dict]:
        """Get employee information for a user."""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        return {
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "department": user.department,
            "position": user.position,
            "join_date": user.join_date,
            "emergency_contact": user.emergency_contact,
            "blood_group": user.blood_group,
            "address": user.address,
            "skills": user.skills,
            "notes": user.notes,
            "birth_date": user.birth_date,
            "info_complete": user.info_complete,
            "info_updated_at": user.info_updated_at,
        }
    
    async def get_incomplete_profiles(self) -> List[User]:
        """Get users with incomplete employee information."""
        return await self.db.get_incomplete_profiles()
    
    # Birthday Methods
    
    async def update_birthday(self, user_id: int, birth_date: str, birth_day: int, 
                             birth_month: int, birth_year: Optional[int] = None) -> None:
        """Update user's birthday information."""
        await self.db.update_birthday(user_id, birth_date, birth_day, birth_month, birth_year)
    
    async def get_users_with_birthday_today(self) -> List[User]:
        """Get all users with birthday today."""
        return await self.db.get_users_with_birthday_today()
    
    async def get_users_with_birthday_tomorrow(self) -> List[User]:
        """Get all users with birthday tomorrow."""
        return await self.db.get_users_with_birthday_tomorrow()
    
    async def get_upcoming_birthdays(self, days: int = 30) -> List[User]:
        """Get users with birthdays in the next N days."""
        return await self.db.get_upcoming_birthdays(days)
    
    async def mark_birthday_wishes_sent(self, user_id: int, date_str: str) -> None:
        """Mark that birthday wishes were sent to user."""
        await self.db.mark_birthday_wishes_sent(user_id, date_str)
    
    async def mark_birthday_reminder_sent(self, user_id: int, date_str: str) -> None:
        """Mark that birthday reminder was sent."""
        await self.db.mark_birthday_reminder_sent(user_id, date_str)
    
    async def set_custom_birthday_message(self, user_id: int, message: str) -> None:
        """Set custom birthday message for user."""
        await self.db.set_custom_birthday_message(user_id, message)
    
    async def clear_custom_birthday_message(self, user_id: int) -> None:
        """Clear custom birthday message."""
        await self.db.clear_custom_birthday_message(user_id)
    
    # Birthday Wishes Log Methods
    
    async def log_birthday_wish(self, user_id: int, wish_date: str, wish_type: str,
                                custom_message: Optional[str] = None,
                                sent_by_user_id: Optional[int] = None,
                                dm_sent: bool = False, group_sent: bool = False) -> None:
        """Log a birthday wish in the database."""
        await self.db.log_birthday_wish(
            user_id, wish_date, wish_type, custom_message,
            sent_by_user_id, dm_sent, group_sent
        )
    
    async def log_birthday_reminder(self, user_id: int, reminder_date: str, birthday_date: str,
                                    user_dm_sent: bool = False, admin_dm_sent: bool = False,
                                    group_sent: bool = False) -> None:
        """Log a birthday reminder in the database."""
        await self.db.log_birthday_reminder(
            user_id, reminder_date, birthday_date,
            user_dm_sent, admin_dm_sent, group_sent
        )
    
    async def get_birthday_wishes_for_user(self, user_id: int) -> List[dict]:
        """Get all birthday wishes sent to a user."""
        return await self.db.get_birthday_wishes_for_user(user_id)
    
    async def get_birthday_reminders_for_user(self, user_id: int) -> List[dict]:
        """Get all birthday reminders sent for a user."""
        return await self.db.get_birthday_reminders_for_user(user_id)
