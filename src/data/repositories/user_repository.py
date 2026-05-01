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
