"""Time and timezone utilities."""

from datetime import datetime, timedelta
from typing import Optional
import pytz
from dateutil import parser as date_parser


def get_timezone(tz_string: str = "GMT+6") -> pytz.timezone:
    """
    Get timezone object from string.
    
    Args:
        tz_string: Timezone string (e.g., "GMT+6", "Asia/Dhaka")
    
    Returns:
        Timezone object
    """
    # Handle GMT+X format
    if tz_string.startswith("GMT"):
        offset_str = tz_string[3:]  # Remove "GMT"
        if offset_str:
            try:
                offset_hours = int(offset_str)
                # Create fixed offset timezone
                return pytz.FixedOffset(offset_hours * 60)
            except ValueError:
                pass
    
    # Try standard timezone name
    try:
        return pytz.timezone(tz_string)
    except pytz.UnknownTimeZoneError:
        # Default to UTC
        return pytz.UTC


def now_in_timezone(tz_string: str = "GMT+6") -> datetime:
    """
    Get current time in specified timezone.
    
    Args:
        tz_string: Timezone string
    
    Returns:
        Current datetime in specified timezone
    """
    tz = get_timezone(tz_string)
    return datetime.now(tz)


def format_time_ago(dt: datetime, reference: Optional[datetime] = None) -> str:
    """
    Format datetime as "time ago" string.
    
    Args:
        dt: Datetime to format
        reference: Reference datetime (default: now)
    
    Returns:
        Formatted string (e.g., "2h ago", "3d ago", "1w ago")
    """
    if reference is None:
        reference = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    
    # Ensure both datetimes are timezone-aware or naive
    if dt.tzinfo is None and reference.tzinfo is not None:
        dt = dt.replace(tzinfo=reference.tzinfo)
    elif dt.tzinfo is not None and reference.tzinfo is None:
        reference = reference.replace(tzinfo=dt.tzinfo)
    
    delta = reference - dt
    
    # Calculate time components
    seconds = delta.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = hours / 24
    weeks = days / 7
    
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif minutes < 60:
        return f"{int(minutes)}m ago"
    elif hours < 24:
        return f"{int(hours)}h ago"
    elif days < 7:
        return f"{int(days)}d ago"
    else:
        return f"{int(weeks)}w ago"


def parse_time_string(time_str: str) -> tuple[int, int]:
    """
    Parse time string in HH:MM format.
    
    Args:
        time_str: Time string (e.g., "09:30")
    
    Returns:
        Tuple of (hour, minute)
    
    Raises:
        ValueError: If format is invalid
    """
    parts = time_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM")
    
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        
        if not (0 <= hour <= 23):
            raise ValueError(f"Invalid hour: {hour}. Must be 0-23")
        if not (0 <= minute <= 59):
            raise ValueError(f"Invalid minute: {minute}. Must be 0-59")
        
        return hour, minute
    except ValueError as e:
        raise ValueError(f"Invalid time format: {time_str}. {e}")


def is_time_after(time_str: str, reference_time: datetime, tz_string: str = "GMT+6") -> bool:
    """
    Check if current time is after specified time.
    
    Args:
        time_str: Time string in HH:MM format
        reference_time: Reference datetime
        tz_string: Timezone string
    
    Returns:
        True if current time is after specified time
    """
    hour, minute = parse_time_string(time_str)
    tz = get_timezone(tz_string)
    
    # Get reference time in specified timezone
    if reference_time.tzinfo is None:
        reference_time = tz.localize(reference_time)
    else:
        reference_time = reference_time.astimezone(tz)
    
    # Create target time for today
    target_time = reference_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    return reference_time >= target_time


def get_day_start(dt: datetime, tz_string: str = "GMT+6") -> datetime:
    """
    Get start of day (00:00:00) for given datetime.
    
    Args:
        dt: Datetime
        tz_string: Timezone string
    
    Returns:
        Start of day datetime
    """
    tz = get_timezone(tz_string)
    
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    else:
        dt = dt.astimezone(tz)
    
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_day_end(dt: datetime, tz_string: str = "GMT+6") -> datetime:
    """
    Get end of day (23:59:59) for given datetime.
    
    Args:
        dt: Datetime
        tz_string: Timezone string
    
    Returns:
        End of day datetime
    """
    tz = get_timezone(tz_string)
    
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    else:
        dt = dt.astimezone(tz)
    
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def get_week_start(dt: datetime, tz_string: str = "GMT+6") -> datetime:
    """
    Get start of week (Monday 00:00:00) for given datetime.
    
    Args:
        dt: Datetime
        tz_string: Timezone string
    
    Returns:
        Start of week datetime
    """
    day_start = get_day_start(dt, tz_string)
    days_since_monday = day_start.weekday()
    return day_start - timedelta(days=days_since_monday)


def get_week_end(dt: datetime, tz_string: str = "GMT+6") -> datetime:
    """
    Get end of week (Sunday 23:59:59) for given datetime.
    
    Args:
        dt: Datetime
        tz_string: Timezone string
    
    Returns:
        End of week datetime
    """
    week_start = get_week_start(dt, tz_string)
    return get_day_end(week_start + timedelta(days=6), tz_string)


def parse_date_string(date_str: str) -> datetime:
    """
    Parse date string in various formats.
    
    Args:
        date_str: Date string (e.g., "2024-01-15", "Jan 15, 2024")
    
    Returns:
        Parsed datetime
    
    Raises:
        ValueError: If format is invalid
    """
    try:
        return date_parser.parse(date_str)
    except Exception as e:
        raise ValueError(f"Invalid date format: {date_str}. {e}")


def format_date(dt: datetime, format_str: str = "%B %d, %Y") -> str:
    """
    Format datetime as string.
    
    Args:
        dt: Datetime to format
        format_str: Format string (default: "Month DD, YYYY")
    
    Returns:
        Formatted date string
    """
    return dt.strftime(format_str)


def format_datetime(dt: datetime, format_str: str = "%B %d, %Y %H:%M") -> str:
    """
    Format datetime as string with time.
    
    Args:
        dt: Datetime to format
        format_str: Format string (default: "Month DD, YYYY HH:MM")
    
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def calculate_hours_between(start: datetime, end: datetime) -> float:
    """
    Calculate hours between two datetimes.
    
    Args:
        start: Start datetime
        end: End datetime
    
    Returns:
        Hours as float
    """
    delta = end - start
    return delta.total_seconds() / 3600
