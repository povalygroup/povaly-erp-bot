"""Message formatting utilities."""


def format_user_mention(user_id: int, username: str) -> str:
    """Format user mention."""
    return f"@{username}" if username else f"User {user_id}"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_ticket_list(tickets: list, with_links: bool = False) -> str:
    """Format list of tickets."""
    if not tickets:
        return "No tickets"
    return "\n".join(f"• {ticket}" for ticket in tickets)
