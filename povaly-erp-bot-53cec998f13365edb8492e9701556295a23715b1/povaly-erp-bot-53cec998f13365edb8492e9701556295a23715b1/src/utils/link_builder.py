"""Telegram message link builder."""


def build_message_link(group_id: int, message_id: int) -> str:
    """
    Build Telegram message link.
    
    Args:
        group_id: Telegram group ID (negative number)
        message_id: Message ID
    
    Returns:
        Clickable message link
    """
    # Remove the -100 prefix from group ID for link
    clean_group_id = str(abs(group_id))[3:] if str(abs(group_id)).startswith("100") else str(abs(group_id))
    return f"https://t.me/c/{clean_group_id}/{message_id}"
