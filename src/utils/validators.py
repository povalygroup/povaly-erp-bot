"""Input validation functions."""

import re
from typing import Optional


def validate_ticket_format(ticket: str, pattern: str) -> bool:
    """Validate ticket format against regex pattern."""
    return bool(re.match(pattern, ticket))


def validate_brand_code(brand: str, valid_brands: list) -> bool:
    """Validate brand code."""
    return brand in valid_brands


def extract_username(text: str) -> Optional[str]:
    """Extract @username from text."""
    match = re.search(r'@(\w+)', text)
    return match.group(1) if match else None


def extract_all_usernames(text: str) -> list:
    """Extract all @usernames from text."""
    return re.findall(r'@(\w+)', text)
