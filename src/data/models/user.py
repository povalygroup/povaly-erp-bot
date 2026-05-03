"""User data model."""

from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from typing import Optional
import re


class UserRole(str, Enum):
    """User role enumeration."""
    
    REGULAR = "regular"
    QA_REVIEWER = "qa_reviewer"
    MANAGER = "manager"
    ADMIN = "admin"
    OWNER = "owner"


@dataclass
class User:
    """User data model."""
    
    # Basic Telegram info
    user_id: int  # Telegram user ID (primary key)
    username: str
    first_name: str  # Telegram first name
    last_name: Optional[str] = None  # Telegram last name
    
    # Employee information
    full_name: Optional[str] = None  # Full legal name
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    join_date: Optional[str] = None  # Format: DD-MM-YYYY
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    skills: Optional[str] = None  # Comma-separated
    notes: Optional[str] = None
    
    # Birthday information
    birth_date: Optional[str] = None  # Format: DD-MM or DD-MM-YYYY
    birth_day: Optional[int] = None  # Day (1-31)
    birth_month: Optional[int] = None  # Month (1-12)
    birth_year: Optional[int] = None  # Year (optional)
    birthday_wishes_sent: Optional[str] = None  # Last wish date YYYY-MM-DD
    custom_birthday_message: Optional[str] = None
    birthday_reminder_sent: Optional[str] = None  # Last reminder date YYYY-MM-DD
    
    # System fields
    role: UserRole = UserRole.REGULAR
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    is_on_leave: bool = False
    leave_start: Optional[datetime] = None
    leave_end: Optional[datetime] = None
    
    # Metadata
    info_set_by: Optional[str] = None  # "self" or "admin"
    info_updated_at: Optional[datetime] = None
    info_complete: bool = False
    
    def get_display_name(self) -> str:
        """Get display name with priority: full_name > first_name + last_name > first_name > username."""
        if self.full_name:
            return self.full_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        return f"@{self.username}" if self.username else "User"
    
    def get_age(self) -> Optional[int]:
        """Calculate age if birth year is available."""
        if not self.birth_year:
            return None
        current_year = datetime.now().year
        age = current_year - self.birth_year
        # Adjust if birthday hasn't occurred this year yet
        if self.birth_month and self.birth_day:
            today = date.today()
            if (self.birth_month, self.birth_day) > (today.month, today.day):
                age -= 1
        return age
    
    def get_days_until_birthday(self) -> Optional[int]:
        """Calculate days until next birthday."""
        if not self.birth_month or not self.birth_day:
            return None
        
        today = date.today()
        # Create birthday date for this year
        try:
            birthday_this_year = date(today.year, self.birth_month, self.birth_day)
        except ValueError:
            # Handle Feb 29 on non-leap years
            birthday_this_year = date(today.year, 2, 28)
        
        # If birthday already passed this year, calculate for next year
        if birthday_this_year < today:
            try:
                birthday_next = date(today.year + 1, self.birth_month, self.birth_day)
            except ValueError:
                birthday_next = date(today.year + 1, 2, 28)
            days_until = (birthday_next - today).days
        else:
            days_until = (birthday_this_year - today).days
        
        return days_until
    
    def is_birthday_today(self) -> bool:
        """Check if today is user's birthday."""
        if not self.birth_month or not self.birth_day:
            return False
        today = date.today()
        return self.birth_month == today.month and self.birth_day == today.day
    
    def is_birthday_tomorrow(self) -> bool:
        """Check if tomorrow is user's birthday."""
        if not self.birth_month or not self.birth_day:
            return False
        days_until = self.get_days_until_birthday()
        return days_until == 1 if days_until is not None else False
    
    def get_birthday_display(self) -> Optional[str]:
        """Get formatted birthday string."""
        if not self.birth_month or not self.birth_day:
            return None
        
        months = ["", "January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        
        month_name = months[self.birth_month]
        day_suffix = self._get_day_suffix(self.birth_day)
        
        if self.birth_year:
            return f"{month_name} {self.birth_day}{day_suffix}, {self.birth_year}"
        else:
            return f"{month_name} {self.birth_day}{day_suffix}"
    
    def _get_day_suffix(self, day: int) -> str:
        """Get ordinal suffix for day (st, nd, rd, th)."""
        if 10 <= day % 100 <= 20:
            return "th"
        else:
            return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    
    def is_info_complete_check(self, required_fields: list) -> bool:
        """Check if all required employee info fields are filled."""
        field_map = {
            "NAME": self.full_name,
            "BIRTHDAY": self.birth_date,
            "EMAIL": self.email,
            "PHONE": self.phone,
            "DEPARTMENT": self.department,
            "POSITION": self.position,
            "JOIN_DATE": self.join_date,
            "EMERGENCY_CONTACT": self.emergency_contact,
            "BLOOD_GROUP": self.blood_group,
        }
        
        for field in required_fields:
            if field in field_map and not field_map[field]:
                return False
        return True
    
    def get_missing_fields(self, required_fields: list) -> list:
        """Get list of missing required fields."""
        field_map = {
            "NAME": self.full_name,
            "BIRTHDAY": self.birth_date,
            "EMAIL": self.email,
            "PHONE": self.phone,
            "DEPARTMENT": self.department,
            "POSITION": self.position,
            "JOIN_DATE": self.join_date,
            "EMERGENCY_CONTACT": self.emergency_contact,
            "BLOOD_GROUP": self.blood_group,
        }
        
        missing = []
        for field in required_fields:
            if field in field_map and not field_map[field]:
                missing.append(field)
        return missing
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone format (basic check)."""
        if not phone:
            return False
        # Allow +, digits, spaces, hyphens, parentheses
        pattern = r'^[\+\d\s\-\(\)]+$'
        return bool(re.match(pattern, phone)) and len(re.sub(r'[^\d]', '', phone)) >= 7
    
    @staticmethod
    def validate_blood_group(blood_group: str) -> bool:
        """Validate blood group."""
        if not blood_group:
            return False
        valid_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        return blood_group.upper() in valid_groups
    
    @staticmethod
    def validate_date_format(date_str: str, format_type: str = "birthday") -> bool:
        """Validate date format (DD-MM or DD-MM-YYYY for birthday, DD-MM-YYYY for join_date)."""
        if not date_str:
            return False
        
        if format_type == "birthday":
            # Accept DD-MM or DD-MM-YYYY
            pattern = r'^\d{2}-\d{2}(-\d{4})?$'
        else:
            # Accept DD-MM-YYYY only
            pattern = r'^\d{2}-\d{2}-\d{4}$'
        
        if not re.match(pattern, date_str):
            return False
        
        # Validate day and month ranges
        parts = date_str.split('-')
        day = int(parts[0])
        month = int(parts[1])
        
        if not (1 <= day <= 31 and 1 <= month <= 12):
            return False
        
        # Validate year if present
        if len(parts) == 3:
            year = int(parts[2])
            if not (1900 <= year <= datetime.now().year):
                return False
        
        return True
    
    @staticmethod
    def parse_birthday(birth_date_str: str) -> tuple:
        """Parse birthday string and return (day, month, year)."""
        if not birth_date_str:
            return (None, None, None)
        
        parts = birth_date_str.split('-')
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2]) if len(parts) == 3 else None
        
        return (day, month, year)
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "position": self.position,
            "join_date": self.join_date,
            "emergency_contact": self.emergency_contact,
            "blood_group": self.blood_group,
            "address": self.address,
            "skills": self.skills,
            "notes": self.notes,
            "birth_date": self.birth_date,
            "birth_day": self.birth_day,
            "birth_month": self.birth_month,
            "birth_year": self.birth_year,
            "birthday_wishes_sent": self.birthday_wishes_sent,
            "custom_birthday_message": self.custom_birthday_message,
            "birthday_reminder_sent": self.birthday_reminder_sent,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "is_on_leave": self.is_on_leave,
            "leave_start": self.leave_start.isoformat() if self.leave_start else None,
            "leave_end": self.leave_end.isoformat() if self.leave_end else None,
            "info_set_by": self.info_set_by,
            "info_updated_at": self.info_updated_at.isoformat() if self.info_updated_at else None,
            "info_complete": self.info_complete,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create user from dictionary."""
        return cls(
            user_id=data["user_id"],
            username=data.get("username", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name"),
            full_name=data.get("full_name"),
            email=data.get("email"),
            phone=data.get("phone"),
            department=data.get("department"),
            position=data.get("position"),
            join_date=data.get("join_date"),
            emergency_contact=data.get("emergency_contact"),
            blood_group=data.get("blood_group"),
            address=data.get("address"),
            skills=data.get("skills"),
            notes=data.get("notes"),
            birth_date=data.get("birth_date"),
            birth_day=data.get("birth_day"),
            birth_month=data.get("birth_month"),
            birth_year=data.get("birth_year"),
            birthday_wishes_sent=data.get("birthday_wishes_sent"),
            custom_birthday_message=data.get("custom_birthday_message"),
            birthday_reminder_sent=data.get("birthday_reminder_sent"),
            role=UserRole(data.get("role", "regular")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            last_active=datetime.fromisoformat(data["last_active"]) if data.get("last_active") else None,
            is_on_leave=data.get("is_on_leave", False),
            leave_start=datetime.fromisoformat(data["leave_start"]) if data.get("leave_start") else None,
            leave_end=datetime.fromisoformat(data["leave_end"]) if data.get("leave_end") else None,
            info_set_by=data.get("info_set_by"),
            info_updated_at=datetime.fromisoformat(data["info_updated_at"]) if data.get("info_updated_at") else None,
            info_complete=data.get("info_complete", False),
        )
