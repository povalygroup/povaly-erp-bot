"""Access control for role-based permissions."""

from src.data.models import UserRole
from src.config import Config


class AccessControl:
    """Role-based access control."""
    
    def __init__(self, config: Config):
        """Initialize access control with configuration."""
        self.config = config
    
    def get_user_role(self, user_id: int) -> UserRole:
        """Get role for a user."""
        if user_id in self.config.ADMINISTRATORS or user_id in self.config.OWNERS:
            return UserRole.ADMIN
        elif user_id in self.config.MANAGERS:
            return UserRole.MANAGER
        elif user_id in self.config.QA_REVIEWERS:
            return UserRole.QA_REVIEWER
        else:
            return UserRole.REGULAR
    
    def can_approve_qa(self, user_id: int) -> bool:
        """Check if user can approve/reject QA submissions."""
        return user_id in self.config.QA_REVIEWERS or self.get_user_role(user_id) in [UserRole.ADMIN, UserRole.MANAGER]
    
    def can_approve_leave(self, user_id: int) -> bool:
        """Check if user can approve leave requests."""
        return self.get_user_role(user_id) in [UserRole.ADMIN, UserRole.MANAGER]
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id in self.config.ADMINISTRATORS or user_id in self.config.OWNERS
