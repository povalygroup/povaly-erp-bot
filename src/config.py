"""Configuration management for the Telegram Operations Automation System."""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """System configuration loaded from environment variables."""

    # Bot Configuration
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_GROUP_ID: int

    # Database Configuration
    DATABASE_TYPE: str = "sqlite"
    DATABASE_PATH: str = "./data/povaly_bot.db"
    DATABASE_BACKUP_TIME: str = "23:00"
    MONGO_URI: Optional[str] = None
    MONGO_DATABASE: Optional[str] = None
    JSON_STORAGE_PATH: Optional[str] = None

    # Timezone
    TIMEZONE: str = "GMT+6"

    # Topic IDs
    TOPIC_OFFICIAL_DIRECTIVES: int = 0
    TOPIC_BRAND_REPOSITORY: int = 0
    TOPIC_TASK_ALLOCATION: int = 0
    TOPIC_CORE_OPERATIONS: int = 0
    TOPIC_QA_REVIEW: int = 0
    TOPIC_CENTRAL_ARCHIVE: int = 0
    TOPIC_DAILY_SYNC: int = 0
    TOPIC_ATTENDANCE_LEAVE: int = 0
    TOPIC_ADMIN_CONTROL_PANEL: int = 0
    TOPIC_BOARDROOM: int = 0
    TOPIC_STRATEGIC_LOUNGE: int = 0
    TOPIC_TRASH: int = 0

    # User Roles (Telegram User IDs)
    ADMINISTRATORS: List[int] = field(default_factory=list)
    MANAGERS: List[int] = field(default_factory=list)
    QA_REVIEWERS: List[int] = field(default_factory=list)
    OWNERS: List[int] = field(default_factory=list)
    
    # Admin DM Recipients (subset of admins who want daily summaries)
    ADMIN_DM_RECIPIENTS: List[int] = field(default_factory=list)

    # Inactivity Thresholds (Hours)
    INACTIVITY_WARNING_HOURS: int = 18
    INACTIVITY_MARK_HOURS: int = 24
    INACTIVITY_ESCALATE_HOURS: int = 48
    INACTIVITY_CRITICAL_HOURS: int = 72
    
    # Task Escalation (Hours)
    TASK_ESCALATION_HOURS: int = 72

    # Attendance Configuration
    ATTENDANCE_LATE_CHECKIN_TIME: str = "11:00"
    ATTENDANCE_AUTO_CHECKOUT_TIME: str = "23:59"
    ATTENDANCE_EXPECTED_CHECKOUT_TIME: str = "17:00"
    ATTENDANCE_MAX_BREAK_TIME_MINUTES: int = 90
    ATTENDANCE_MAX_BREAK_COUNT: int = 5
    ATTENDANCE_LATE_CHECKIN_ALERT_COUNT: int = 3  # Alert after 3 late check-ins in a week
    ATTENDANCE_MISSING_CHECKIN_ALERT_TIME: str = "12:15"  # Alert time for missing check-ins
    
    # QA Escalation (Hours)
    QA_ESCALATION_HOURS: int = 24
    QA_REMINDER_HOURS: int = 12
    
    # Format Violation Tracking
    VIOLATION_ALERT_THRESHOLD: int = 3  # Alert admins after 3 violations in same day

    # Report Scheduling
    DAILY_REPORT_TIME: str = "22:30"
    WEEKLY_REPORT_DAY: str = "Sunday"
    WEEKLY_REPORT_TIME: str = "22:30"
    DAILY_SUMMARY_TIME: str = "00:00"
    DAILY_SUMMARY_HOUR: int = 0  # 0 = midnight
    DAILY_SUMMARY_MINUTE: int = 0

    # Violation Handling
    VIOLATION_AUTO_DELETE_MALFORMED: bool = True
    VIOLATION_REPEATED_THRESHOLD: int = 3
    VIOLATION_REPEATED_ACTION: str = "escalate_to_manager"

    # Brand Codes
    BRAND_CODES: List[str] = field(default_factory=list)

    # Ticket Format Validation
    TICKET_FORMAT_REGEX: str = r"^[A-Z]{2}-\d{4}-\d+$"

    # Notification Preferences
    NOTIFICATION_SEND_DM: bool = True
    NOTIFICATION_SEND_TOPIC_ALERTS: bool = True
    NOTIFICATION_INCLUDE_MESSAGE_LINKS: bool = True

    # Performance Monitoring
    PERFORMANCE_QA_REJECTION_THRESHOLD: float = 0.5
    PERFORMANCE_DORMANCY_DAYS: int = 7
    PERFORMANCE_LATE_CHECKIN_THRESHOLD: int = 5

    # Security
    DATABASE_ENCRYPTION_KEY: str = ""
    LOG_RETENTION_DAYS: int = 30
    AUDIT_TRAIL_RETENTION_DAYS: int = 90

    # Feature Flags
    FEATURE_AUTO_CHECKOUT: bool = True
    FEATURE_AUTO_REMEDIATION: bool = True
    FEATURE_PREDICTIVE_ALERTS: bool = True
    FEATURE_ANALYTICS_DASHBOARD: bool = True
    FEATURE_DAILY_SUMMARY: bool = True

    @classmethod
    def load_from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()

        # Validate required parameters
        required_params = [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_GROUP_ID",
            "DATABASE_ENCRYPTION_KEY",
        ]

        missing_params = []
        for param in required_params:
            if not os.getenv(param):
                missing_params.append(param)

        if missing_params:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_params)}\n"
                f"Please check your .env file and ensure all required parameters are set.\n"
                f"See .env.template for reference."
            )

        # Parse user role lists
        def parse_user_ids(env_var: str) -> List[int]:
            value = os.getenv(env_var, "")
            if not value:
                return []
            try:
                return [int(uid.strip()) for uid in value.split(",") if uid.strip()]
            except ValueError:
                raise ValueError(
                    f"Invalid user ID format in {env_var}. "
                    f"Expected comma-separated integers."
                )

        # Parse brand codes
        def parse_brand_codes(env_var: str) -> List[str]:
            value = os.getenv(env_var, "")
            if not value:
                return []
            return [code.strip() for code in value.split(",") if code.strip()]

        # Parse boolean values
        def parse_bool(env_var: str, default: bool) -> bool:
            value = os.getenv(env_var, str(default)).lower()
            return value in ("true", "1", "yes", "on")

        # Parse integer with default
        def parse_int(env_var: str, default: int) -> int:
            value = os.getenv(env_var)
            if value is None:
                return default
            try:
                return int(value)
            except ValueError:
                raise ValueError(
                    f"Invalid integer value for {env_var}: {value}"
                )

        # Parse float with default
        def parse_float(env_var: str, default: float) -> float:
            value = os.getenv(env_var)
            if value is None:
                return default
            try:
                return float(value)
            except ValueError:
                raise ValueError(
                    f"Invalid float value for {env_var}: {value}"
                )

        # Validate time format (HH:MM)
        def validate_time_format(time_str: str, param_name: str) -> str:
            if not re.match(r"^\d{2}:\d{2}$", time_str):
                raise ValueError(
                    f"Invalid time format for {param_name}: {time_str}. "
                    f"Expected HH:MM format (e.g., 09:30)"
                )
            return time_str

        # Validate ticket format regex
        ticket_regex = os.getenv("TICKET_FORMAT_REGEX", r"^[A-Z]{2}-\d{4}-\d+$")
        try:
            re.compile(ticket_regex)
        except re.error as e:
            raise ValueError(
                f"Invalid regex pattern for TICKET_FORMAT_REGEX: {ticket_regex}\n"
                f"Error: {e}"
            )

        # Validate violation action
        violation_action = os.getenv("VIOLATION_REPEATED_ACTION", "escalate_to_manager")
        valid_actions = ["escalate_to_manager", "log_only", "temporary_restriction"]
        if violation_action not in valid_actions:
            raise ValueError(
                f"Invalid VIOLATION_REPEATED_ACTION: {violation_action}. "
                f"Must be one of: {', '.join(valid_actions)}"
            )

        # Validate database type
        db_type = os.getenv("DATABASE_TYPE", "sqlite")
        valid_db_types = ["sqlite", "mongodb", "json"]
        if db_type not in valid_db_types:
            raise ValueError(
                f"Invalid DATABASE_TYPE: {db_type}. "
                f"Must be one of: {', '.join(valid_db_types)}"
            )

        # Validate encryption key length
        encryption_key = os.getenv("DATABASE_ENCRYPTION_KEY", "")
        if len(encryption_key) < 32:
            raise ValueError(
                "DATABASE_ENCRYPTION_KEY must be at least 32 characters long. "
                "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )

        return cls(
            # Bot Configuration
            TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            TELEGRAM_GROUP_ID=int(os.getenv("TELEGRAM_GROUP_ID", "0")),
            
            # Database Configuration
            DATABASE_TYPE=db_type,
            DATABASE_PATH=os.getenv("DATABASE_PATH", "./data/povaly_bot.db"),
            DATABASE_BACKUP_TIME=validate_time_format(
                os.getenv("DATABASE_BACKUP_TIME", "23:00"),
                "DATABASE_BACKUP_TIME"
            ),
            MONGO_URI=os.getenv("MONGO_URI"),
            MONGO_DATABASE=os.getenv("MONGO_DATABASE"),
            JSON_STORAGE_PATH=os.getenv("JSON_STORAGE_PATH"),
            
            # Timezone
            TIMEZONE=os.getenv("TIMEZONE", "GMT+6"),
            
            # Topic IDs
            TOPIC_OFFICIAL_DIRECTIVES=parse_int("TOPIC_OFFICIAL_DIRECTIVES", 0),
            TOPIC_BRAND_REPOSITORY=parse_int("TOPIC_BRAND_REPOSITORY", 0),
            TOPIC_TASK_ALLOCATION=parse_int("TOPIC_TASK_ALLOCATION", 0),
            TOPIC_CORE_OPERATIONS=parse_int("TOPIC_CORE_OPERATIONS", 0),
            TOPIC_QA_REVIEW=parse_int("TOPIC_QA_REVIEW", 0),
            TOPIC_CENTRAL_ARCHIVE=parse_int("TOPIC_CENTRAL_ARCHIVE", 0),
            TOPIC_DAILY_SYNC=parse_int("TOPIC_DAILY_SYNC", 0),
            TOPIC_ATTENDANCE_LEAVE=parse_int("TOPIC_ATTENDANCE_LEAVE", 0),
            TOPIC_ADMIN_CONTROL_PANEL=parse_int("TOPIC_ADMIN_CONTROL_PANEL", 0),
            TOPIC_BOARDROOM=parse_int("TOPIC_BOARDROOM", 0),
            TOPIC_STRATEGIC_LOUNGE=parse_int("TOPIC_STRATEGIC_LOUNGE", 0),
            TOPIC_TRASH=parse_int("TOPIC_TRASH", 0),
            
            # User Roles
            ADMINISTRATORS=parse_user_ids("ADMINISTRATORS"),
            MANAGERS=parse_user_ids("MANAGERS"),
            QA_REVIEWERS=parse_user_ids("QA_REVIEWERS"),
            OWNERS=parse_user_ids("OWNERS"),
            
            # Admin DM Recipients
            ADMIN_DM_RECIPIENTS=parse_user_ids("ADMIN_DM_RECIPIENTS"),
            
            # Inactivity Thresholds
            INACTIVITY_WARNING_HOURS=parse_int("INACTIVITY_WARNING_HOURS", 18),
            INACTIVITY_MARK_HOURS=parse_int("INACTIVITY_MARK_HOURS", 24),
            INACTIVITY_ESCALATE_HOURS=parse_int("INACTIVITY_ESCALATE_HOURS", 48),
            INACTIVITY_CRITICAL_HOURS=parse_int("INACTIVITY_CRITICAL_HOURS", 72),
            
            # Task Escalation
            TASK_ESCALATION_HOURS=parse_int("TASK_ESCALATION_HOURS", 72),
            
            # Attendance Configuration
            ATTENDANCE_LATE_CHECKIN_TIME=validate_time_format(
                os.getenv("ATTENDANCE_LATE_CHECKIN_TIME", "11:00"),
                "ATTENDANCE_LATE_CHECKIN_TIME"
            ),
            ATTENDANCE_AUTO_CHECKOUT_TIME=validate_time_format(
                os.getenv("ATTENDANCE_AUTO_CHECKOUT_TIME", "23:59"),
                "ATTENDANCE_AUTO_CHECKOUT_TIME"
            ),
            ATTENDANCE_EXPECTED_CHECKOUT_TIME=validate_time_format(
                os.getenv("ATTENDANCE_EXPECTED_CHECKOUT_TIME", "17:00"),
                "ATTENDANCE_EXPECTED_CHECKOUT_TIME"
            ),
            ATTENDANCE_MAX_BREAK_TIME_MINUTES=parse_int("ATTENDANCE_MAX_BREAK_TIME_MINUTES", 90),
            ATTENDANCE_MAX_BREAK_COUNT=parse_int("ATTENDANCE_MAX_BREAK_COUNT", 5),
            ATTENDANCE_LATE_CHECKIN_ALERT_COUNT=parse_int("ATTENDANCE_LATE_CHECKIN_ALERT_COUNT", 3),
            ATTENDANCE_MISSING_CHECKIN_ALERT_TIME=validate_time_format(
                os.getenv("ATTENDANCE_MISSING_CHECKIN_ALERT_TIME", "12:15"),
                "ATTENDANCE_MISSING_CHECKIN_ALERT_TIME"
            ),
            
            # QA Escalation
            QA_ESCALATION_HOURS=parse_int("QA_ESCALATION_HOURS", 24),
            QA_REMINDER_HOURS=parse_int("QA_REMINDER_HOURS", 12),
            
            # Format Violation Tracking
            VIOLATION_ALERT_THRESHOLD=parse_int("VIOLATION_ALERT_THRESHOLD", 3),
            
            # Report Scheduling
            DAILY_REPORT_TIME=validate_time_format(
                os.getenv("DAILY_REPORT_TIME", "22:30"),
                "DAILY_REPORT_TIME"
            ),
            WEEKLY_REPORT_DAY=os.getenv("WEEKLY_REPORT_DAY", "Sunday"),
            WEEKLY_REPORT_TIME=validate_time_format(
                os.getenv("WEEKLY_REPORT_TIME", "22:30"),
                "WEEKLY_REPORT_TIME"
            ),
            DAILY_SUMMARY_TIME=validate_time_format(
                os.getenv("DAILY_SUMMARY_TIME", "00:00"),
                "DAILY_SUMMARY_TIME"
            ),
            # Parse hour and minute from DAILY_SUMMARY_TIME
            DAILY_SUMMARY_HOUR=int(os.getenv("DAILY_SUMMARY_TIME", "00:00").split(":")[0]),
            DAILY_SUMMARY_MINUTE=int(os.getenv("DAILY_SUMMARY_TIME", "00:00").split(":")[1]),
            
            # Violation Handling
            VIOLATION_AUTO_DELETE_MALFORMED=parse_bool("VIOLATION_AUTO_DELETE_MALFORMED", True),
            VIOLATION_REPEATED_THRESHOLD=parse_int("VIOLATION_REPEATED_THRESHOLD", 3),
            VIOLATION_REPEATED_ACTION=violation_action,
            
            # Brand Codes
            BRAND_CODES=parse_brand_codes("BRAND_CODES"),
            
            # Ticket Format Validation
            TICKET_FORMAT_REGEX=ticket_regex,
            
            # Notification Preferences
            NOTIFICATION_SEND_DM=parse_bool("NOTIFICATION_SEND_DM", True),
            NOTIFICATION_SEND_TOPIC_ALERTS=parse_bool("NOTIFICATION_SEND_TOPIC_ALERTS", True),
            NOTIFICATION_INCLUDE_MESSAGE_LINKS=parse_bool("NOTIFICATION_INCLUDE_MESSAGE_LINKS", True),
            
            # Performance Monitoring
            PERFORMANCE_QA_REJECTION_THRESHOLD=parse_float("PERFORMANCE_QA_REJECTION_THRESHOLD", 0.5),
            PERFORMANCE_DORMANCY_DAYS=parse_int("PERFORMANCE_DORMANCY_DAYS", 7),
            PERFORMANCE_LATE_CHECKIN_THRESHOLD=parse_int("PERFORMANCE_LATE_CHECKIN_THRESHOLD", 5),
            
            # Security
            DATABASE_ENCRYPTION_KEY=encryption_key,
            LOG_RETENTION_DAYS=parse_int("LOG_RETENTION_DAYS", 30),
            AUDIT_TRAIL_RETENTION_DAYS=parse_int("AUDIT_TRAIL_RETENTION_DAYS", 90),
            
            # Feature Flags
            FEATURE_AUTO_CHECKOUT=parse_bool("FEATURE_AUTO_CHECKOUT", True),
            FEATURE_AUTO_REMEDIATION=parse_bool("FEATURE_AUTO_REMEDIATION", True),
            FEATURE_PREDICTIVE_ALERTS=parse_bool("FEATURE_PREDICTIVE_ALERTS", True),
            FEATURE_ANALYTICS_DASHBOARD=parse_bool("FEATURE_ANALYTICS_DASHBOARD", True),
            FEATURE_DAILY_SUMMARY=parse_bool("FEATURE_DAILY_SUMMARY", True),
        )

    def validate(self) -> None:
        """Validate configuration after loading."""
        errors = []

        # Validate topic IDs are set
        topic_fields = [
            "TOPIC_OFFICIAL_DIRECTIVES",
            "TOPIC_BRAND_REPOSITORY",
            "TOPIC_TASK_ALLOCATION",
            "TOPIC_CORE_OPERATIONS",
            "TOPIC_QA_REVIEW",
            "TOPIC_CENTRAL_ARCHIVE",
            "TOPIC_DAILY_SYNC",
            "TOPIC_ATTENDANCE_LEAVE",
            "TOPIC_ADMIN_CONTROL_PANEL",
            "TOPIC_BOARDROOM",
            "TOPIC_STRATEGIC_LOUNGE",
            "TOPIC_TRASH",
        ]

        for field_name in topic_fields:
            if getattr(self, field_name) == 0:
                errors.append(f"{field_name} must be set to a valid topic ID")

        # Validate at least one administrator or owner
        if not self.ADMINISTRATORS and not self.OWNERS:
            errors.append("At least one ADMINISTRATOR or OWNER must be configured")

        # Validate brand codes
        if not self.BRAND_CODES:
            errors.append("At least one BRAND_CODE must be configured")

        if errors:
            raise ValueError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load_from_env()
        _config.validate()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment variables."""
    global _config
    _config = Config.load_from_env()
    _config.validate()
    return _config
