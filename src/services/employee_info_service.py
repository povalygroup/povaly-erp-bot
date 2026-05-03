"""Employee Information Service - Handles employee data collection and management."""

import logging
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from src.data.models.user import User

logger = logging.getLogger(__name__)


class EmployeeInfoService:
    """Service for managing employee information."""
    
    def __init__(self, user_repo, config):
        """Initialize employee info service."""
        self.user_repo = user_repo
        self.config = config
        
        # Get required and optional fields from config
        self.required_fields = self._parse_config_fields(
            config.EMPLOYEE_INFO_REQUIRED_FIELDS if hasattr(config, 'EMPLOYEE_INFO_REQUIRED_FIELDS') else "NAME,BIRTHDAY,EMAIL,PHONE"
        )
        self.optional_fields = self._parse_config_fields(
            config.EMPLOYEE_INFO_OPTIONAL_FIELDS if hasattr(config, 'EMPLOYEE_INFO_OPTIONAL_FIELDS') else "DEPARTMENT,POSITION,JOIN_DATE"
        )
    
    def _parse_config_fields(self, fields_str: str) -> List[str]:
        """Parse comma-separated config fields."""
        if not fields_str:
            return []
        return [f.strip().upper() for f in fields_str.split(',') if f.strip()]
    
    def parse_employee_info_from_message(self, text: str) -> Optional[Dict]:
        """
        Parse employee information from message text.
        
        Expected format:
        [EMPLOYEE_INFO]
        [NAME] Full Name
        [BIRTHDAY] DD-MM-YYYY
        [EMAIL] email@example.com
        [PHONE] +1234567890
        [DEPARTMENT] Department Name
        [POSITION] Job Title
        [JOIN_DATE] DD-MM-YYYY
        [EMERGENCY_CONTACT] Name: Phone
        [BLOOD_GROUP] A+
        [ADDRESS] Full Address
        [SKILLS] Skill1, Skill2
        [NOTES] Additional notes
        
        Returns:
            Dict with parsed fields or None if invalid format
        """
        if not text or '[EMPLOYEE_INFO]' not in text:
            return None
        
        try:
            # Extract the employee info block
            start_idx = text.find('[EMPLOYEE_INFO]')
            info_block = text[start_idx:]
            
            # Parse each field
            info_dict = {}
            
            # Define field patterns
            field_patterns = {
                'NAME': r'\[NAME\]\s*(.+?)(?=\n\[|$)',
                'BIRTHDAY': r'\[BIRTHDAY\]\s*(.+?)(?=\n\[|$)',
                'EMAIL': r'\[EMAIL\]\s*(.+?)(?=\n\[|$)',
                'PHONE': r'\[PHONE\]\s*(.+?)(?=\n\[|$)',
                'DEPARTMENT': r'\[DEPARTMENT\]\s*(.+?)(?=\n\[|$)',
                'POSITION': r'\[POSITION\]\s*(.+?)(?=\n\[|$)',
                'JOIN_DATE': r'\[JOIN_DATE\]\s*(.+?)(?=\n\[|$)',
                'EMERGENCY_CONTACT': r'\[EMERGENCY_CONTACT\]\s*(.+?)(?=\n\[|$)',
                'BLOOD_GROUP': r'\[BLOOD_GROUP\]\s*(.+?)(?=\n\[|$)',
                'ADDRESS': r'\[ADDRESS\]\s*(.+?)(?=\n\[|$)',
                'SKILLS': r'\[SKILLS\]\s*(.+?)(?=\n\[|$)',
                'NOTES': r'\[NOTES\]\s*(.+?)(?=\n\[|$)',
            }
            
            # Extract each field
            for field_name, pattern in field_patterns.items():
                match = re.search(pattern, info_block, re.IGNORECASE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    if value:
                        info_dict[field_name] = value
            
            # Map to database field names
            db_info = {
                'full_name': info_dict.get('NAME'),
                'email': info_dict.get('EMAIL'),
                'phone': info_dict.get('PHONE'),
                'department': info_dict.get('DEPARTMENT'),
                'position': info_dict.get('POSITION'),
                'join_date': info_dict.get('JOIN_DATE'),
                'emergency_contact': info_dict.get('EMERGENCY_CONTACT'),
                'blood_group': info_dict.get('BLOOD_GROUP'),
                'address': info_dict.get('ADDRESS'),
                'skills': info_dict.get('SKILLS'),
                'notes': info_dict.get('NOTES'),
                'birth_date': info_dict.get('BIRTHDAY'),
            }
            
            # Parse birthday into components
            if db_info.get('birth_date'):
                birth_day, birth_month, birth_year = User.parse_birthday(db_info['birth_date'])
                db_info['birth_day'] = birth_day
                db_info['birth_month'] = birth_month
                db_info['birth_year'] = birth_year
            
            return db_info
            
        except Exception as e:
            logger.error(f"Error parsing employee info: {e}")
            return None
    
    def validate_employee_info(self, info_dict: Dict) -> Tuple[bool, List[str]]:
        """
        Validate employee information.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            field_map = {
                'NAME': 'full_name',
                'BIRTHDAY': 'birth_date',
                'EMAIL': 'email',
                'PHONE': 'phone',
                'DEPARTMENT': 'department',
                'POSITION': 'position',
                'JOIN_DATE': 'join_date',
                'EMERGENCY_CONTACT': 'emergency_contact',
                'BLOOD_GROUP': 'blood_group',
            }
            
            db_field = field_map.get(field)
            if db_field and not info_dict.get(db_field):
                errors.append(f"Missing required field: {field}")
        
        # Validate email format
        if info_dict.get('email') and not User.validate_email(info_dict['email']):
            errors.append("Invalid email format")
        
        # Validate phone format
        if info_dict.get('phone') and not User.validate_phone(info_dict['phone']):
            errors.append("Invalid phone format (must contain at least 7 digits)")
        
        # Validate blood group
        if info_dict.get('blood_group') and not User.validate_blood_group(info_dict['blood_group']):
            errors.append("Invalid blood group (must be A+, A-, B+, B-, AB+, AB-, O+, or O-)")
        
        # Validate birthday format
        if info_dict.get('birth_date') and not User.validate_date_format(info_dict['birth_date'], 'birthday'):
            errors.append("Invalid birthday format (use DD-MM-YYYY or DD-MM)")
        
        # Validate join date format
        if info_dict.get('join_date') and not User.validate_date_format(info_dict['join_date'], 'join_date'):
            errors.append("Invalid join date format (use DD-MM-YYYY)")
        
        return (len(errors) == 0, errors)
    
    async def save_employee_info(self, user_id: int, info_dict: Dict, set_by: str = "self") -> bool:
        """
        Save employee information to database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate first
            is_valid, errors = self.validate_employee_info(info_dict)
            if not is_valid:
                logger.error(f"Validation failed for user {user_id}: {errors}")
                return False
            
            # Save to database
            await self.user_repo.update_employee_info(user_id, info_dict, set_by)
            
            logger.info(f"Employee info saved for user {user_id} by {set_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving employee info for user {user_id}: {e}")
            return False
    
    def format_employee_info_display(self, user: User) -> str:
        """
        Format employee information for display.
        
        Returns:
            Formatted string with all employee info
        """
        lines = []
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if user.full_name:
            lines.append(f"👤 Name: {user.full_name}")
        
        if user.birth_date:
            birthday_display = user.get_birthday_display()
            age = user.get_age()
            if age:
                lines.append(f"🎂 Birthday: {birthday_display} (Age: {age})")
            else:
                lines.append(f"🎂 Birthday: {birthday_display}")
        
        if user.email:
            lines.append(f"📧 Email: {user.email}")
        
        if user.phone:
            lines.append(f"📱 Phone: {user.phone}")
        
        if user.department:
            lines.append(f"🏢 Department: {user.department}")
        
        if user.position:
            lines.append(f"💼 Position: {user.position}")
        
        if user.join_date:
            lines.append(f"📅 Join Date: {self._format_date_display(user.join_date)}")
        
        if user.emergency_contact:
            lines.append(f"🚨 Emergency: {user.emergency_contact}")
        
        if user.blood_group:
            lines.append(f"🩸 Blood Group: {user.blood_group}")
        
        if user.address:
            lines.append(f"📍 Address: {user.address}")
        
        if user.skills:
            lines.append(f"🎯 Skills: {user.skills}")
        
        if user.notes:
            lines.append(f"📝 Notes: {user.notes}")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
    
    def _format_date_display(self, date_str: str) -> str:
        """Format date string for display (DD-MM-YYYY to Month DD, YYYY)."""
        try:
            parts = date_str.split('-')
            if len(parts) == 3:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                months = ["", "January", "February", "March", "April", "May", "June",
                         "July", "August", "September", "October", "November", "December"]
                return f"{months[month]} {day}, {year}"
            return date_str
        except:
            return date_str
    
    def get_missing_fields(self, user: User) -> List[str]:
        """
        Get list of missing required fields for a user.
        
        Returns:
            List of missing field names
        """
        return user.get_missing_fields(self.required_fields)
    
    def format_info_request_message(self, user: User) -> str:
        """
        Format the employee info request message for first-time users.
        
        Returns:
            Formatted message with instructions
        """
        display_name = user.first_name or user.username or "there"
        
        message = f"""👋 Welcome to Povaly Operations, {display_name}!

Your account has been created successfully! ✅

To complete your employee profile, please provide your information in the following format:

📋 EMPLOYEE INFORMATION FORMAT:

[EMPLOYEE_INFO]
[NAME] Your Full Name
[BIRTHDAY] DD-MM-YYYY
[EMAIL] your.email@example.com
[PHONE] +1234567890
[DEPARTMENT] Your Department
[POSITION] Your Job Title
[JOIN_DATE] DD-MM-YYYY
[EMERGENCY_CONTACT] Contact Name: +1234567890
[BLOOD_GROUP] A+/B+/O+/AB+/A-/B-/O-/AB-
[ADDRESS] Your Address (optional)
[SKILLS] Skill1, Skill2, Skill3 (optional)
[NOTES] Any additional notes (optional)

📌 Example:

[EMPLOYEE_INFO]
[NAME] John Michael Doe
[BIRTHDAY] 15-05-1990
[EMAIL] john.doe@povaly.com
[PHONE] +1234567890
[DEPARTMENT] Development
[POSITION] Senior Developer
[JOIN_DATE] 01-01-2024
[EMERGENCY_CONTACT] Jane Doe: +0987654321
[BLOOD_GROUP] A+
[ADDRESS] 123 Main St, City, Country
[SKILLS] Python, JavaScript, React
[NOTES] Prefers morning shifts

✨ Required fields: {', '.join(self.required_fields)}
📝 Optional fields: {', '.join(self.optional_fields)}

You can:
• Reply with your information now
• Skip by typing /skip (you can update later)
• Update anytime with /updateinfo

Your information is confidential and used only for HR purposes! 🔐"""
        
        return message
    
    def format_update_request_message(self, user: User) -> str:
        """
        Format the employee info update request message.
        
        Returns:
            Formatted message with current info and instructions
        """
        message = "📋 Update Your Employee Information\n\n"
        
        if user.full_name or user.email or user.phone:
            message += "Current information:\n"
            message += self.format_employee_info_display(user)
            message += "\n\n"
        else:
            message += "No information on file.\n\n"
        
        message += """To update, send your information in this format:

[EMPLOYEE_INFO]
[NAME] Your Full Name
[BIRTHDAY] DD-MM-YYYY
[EMAIL] your.email@example.com
[PHONE] +1234567890
[DEPARTMENT] Your Department
[POSITION] Your Job Title
[JOIN_DATE] DD-MM-YYYY
[EMERGENCY_CONTACT] Contact Name: Phone
[BLOOD_GROUP] A+/B+/O+/AB+/A-/B-/O-/AB-
[ADDRESS] Your Address (optional)
[SKILLS] Skill1, Skill2, Skill3 (optional)
[NOTES] Any notes (optional)

Type /cancel to cancel this operation."""
        
        return message
    
    def format_confirmation_message(self, user: User) -> str:
        """
        Format the confirmation message after saving employee info.
        
        Returns:
            Formatted confirmation message
        """
        message = "✅ Employee Information Saved Successfully!\n\n"
        message += "Your profile has been updated:\n"
        message += self.format_employee_info_display(user)
        message += "\n\n"
        
        if user.birth_date:
            days_until = user.get_days_until_birthday()
            if days_until == 0:
                message += "🎉 Today is your birthday! Happy Birthday!\n\n"
            elif days_until == 1:
                message += "🎉 Tomorrow is your birthday! We'll celebrate!\n\n"
            elif days_until is not None:
                message += f"🎉 We'll celebrate your birthday in {days_until} days!\n\n"
        
        message += "You can update your information anytime with /updateinfo"
        
        return message
    
    async def send_info_request_dm(self, context, user: User) -> bool:
        """
        Send employee info request DM to user.
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message = self.format_info_request_message(user)
            
            await context.bot.send_message(
                chat_id=user.user_id,
                text=message,
                parse_mode=None  # Plain text to avoid parsing issues
            )
            
            logger.info(f"Sent employee info request to user {user.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send employee info request to user {user.user_id}: {e}")
            return False
