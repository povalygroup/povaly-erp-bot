"""Utility functions for message handling."""

import logging
import asyncio

logger = logging.getLogger(__name__)


async def send_auto_delete_dm(context, user_id, text, parse_mode='Markdown', 
                               delete_after_seconds=30, disable_web_page_preview=True):
    """
    Send a DM that auto-deletes after specified seconds.
    
    Args:
        context: Telegram context
        user_id: User ID to send DM to
        text: Message text
        parse_mode: Parse mode (Markdown, HTML, None for plain text)
        delete_after_seconds: Seconds before auto-delete
        disable_web_page_preview: Whether to disable link previews
    
    Returns:
        Sent message object or None if failed
    """
    try:
        # Add auto-delete warning to message (format based on parse_mode)
        if parse_mode == 'Markdown':
            warning = f"\n\n_⏱️ This message will auto-delete in {delete_after_seconds} seconds_"
        elif parse_mode == 'HTML':
            warning = f"\n\n<i>⏱️ This message will auto-delete in {delete_after_seconds} seconds</i>"
        else:
            # Plain text (no formatting)
            warning = f"\n\n⏱️ This message will auto-delete in {delete_after_seconds} seconds"
        
        full_text = text + warning
        
        sent_msg = await context.bot.send_message(
            chat_id=user_id,
            text=full_text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview
        )
        
        logger.info(f"Sent auto-delete DM to user {user_id} (delete after {delete_after_seconds}s)")
        
        # Schedule deletion as background task
        async def delete_message_later():
            await asyncio.sleep(delete_after_seconds)
            try:
                await sent_msg.delete()
                logger.info(f"Auto-deleted DM {sent_msg.message_id} after {delete_after_seconds} seconds")
            except Exception as e:
                logger.warning(f"Failed to auto-delete DM: {e}")
        
        asyncio.create_task(delete_message_later())
        
        return sent_msg
        
    except Exception as e:
        logger.error(f"Failed to send auto-delete DM to user {user_id}: {e}")
        return None


async def send_permanent_dm(context, user_id, text, parse_mode='Markdown', 
                            disable_web_page_preview=True):
    """
    Send a permanent DM (no auto-delete).
    Use for educational messages, format errors, important notifications.
    
    Args:
        context: Telegram context
        user_id: User ID to send DM to
        text: Message text
        parse_mode: Parse mode (Markdown, HTML, etc.)
        disable_web_page_preview: Whether to disable link previews
    
    Returns:
        Sent message object or None if failed
    """
    try:
        sent_msg = await context.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview
        )
        
        logger.info(f"Sent permanent DM to user {user_id}")
        return sent_msg
        
    except Exception as e:
        logger.error(f"Failed to send permanent DM to user {user_id}: {e}")
        return None
