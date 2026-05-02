"""Pagination handler for /myissues command."""

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def build_myissues_message(context, issues_by_status, total_issues, chat_id, user_id=None, username=None, title="Your Issues", callback_prefix="myissues_expand"):
    """Build the myissues message with pagination."""
    message = f"📋 **{title}**\n\n"
    
    # Add user info at the top
    if user_id:
        message += f"👤 **User:** @{username or 'unknown'}\n"
        message += f"🆔 **ID:** {user_id}\n\n"
    
    # Status order
    status_order = ['open', 'in_progress', 'resolved', 'escalated', 'invalid']
    status_emojis = {
        'open': '🔴',
        'in_progress': '🟡',
        'resolved': '✅',
        'escalated': '🚨',
        'invalid': '❌'
    }
    status_labels = {
        'open': 'OPEN',
        'in_progress': 'IN PROGRESS',
        'resolved': 'RESOLVED',
        'escalated': 'ESCALATED',
        'invalid': 'INVALID'
    }
    
    # Get config and pagination data
    config = context.bot_data.get('config')
    topic_id = config.TOPIC_CORE_OPERATIONS if config else None
    
    # Determine which data key to use based on callback_prefix
    if callback_prefix == "myclaimedissues_expand":
        data_key = 'myclaimedissues_data'
    else:
        data_key = 'myissues_data'
    
    myissues_data = context.user_data.get(data_key, {})
    page_size = myissues_data.get('page_size', 5)
    expanded_statuses = myissues_data.get('expanded_statuses', set())
    
    # Build keyboard for "Show more" buttons
    keyboard_buttons = []
    
    for status in status_order:
        if status in issues_by_status:
            issues = issues_by_status[status]
            emoji = status_emojis.get(status, '•')
            label = status_labels.get(status, status.upper())
            message += f"{emoji} **{label}** ({len(issues)})\n"
            
            # Determine how many issues to show
            if status in expanded_statuses:
                # Show all issues
                issues_to_show = issues
            else:
                # Show only first page_size issues
                issues_to_show = issues[:page_size]
            
            # Build links for issues
            for issue in issues_to_show:
                # Create proper link format to the specific issue message
                chat_id_str = str(chat_id)
                if chat_id_str.startswith('-100'):
                    group_id = chat_id_str[4:]
                else:
                    group_id = chat_id_str.lstrip('-')
                
                # Build link to the specific message
                if topic_id:
                    link = f"https://t.me/c/{group_id}/{topic_id}/{issue.message_id}"
                else:
                    link = f"https://t.me/c/{group_id}/{issue.message_id}"
                
                # Priority emoji
                priority_emoji = {
                    'LOW': '🟢',
                    'MEDIUM': '🟡',
                    'HIGH': '🟠',
                    'CRITICAL': '🔴'
                }.get(issue.priority.value, '❓')
                
                message += f"  • <a href='{link}'>#{issue.issue_ticket}</a> {priority_emoji} - {issue.title}\n"
            
            # Add "Show more" button if there are more issues
            if len(issues) > page_size and status not in expanded_statuses:
                remaining = len(issues) - page_size
                message += f"  • _... and {remaining} more_\n"
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"Show {remaining} more {label} issues",
                        callback_data=f"{callback_prefix}:{status}"
                    )
                ])
            
            message += "\n"
    
    message += f"**Total:** {total_issues} issues\n\n"
    message += "**Status Legend:** 🔴 Open | 🟡 In Progress | ✅ Resolved | 🚨 Escalated | ❌ Invalid\n"
    message += "**Priority Legend:** 🟢 Low | 🟡 Medium | 🟠 High | 🔴 Critical\n\n"
    message += "⚠️ _This message will auto-delete in 40 seconds. React with 👏 to keep it for 10 minutes._"
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(keyboard_buttons) if keyboard_buttons else None
    
    return message, keyboard


async def handle_myissues_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pagination button clicks for /myissues and /myclaimedissues."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    parts = query.data.split(':', 2)
    action = parts[0]
    status = parts[1] if len(parts) > 1 else None
    
    # Determine which command this is for
    if action == "myissues_expand":
        data_key = 'myissues_data'
        delete_task_key = 'myissues_delete_task'
        title = "Your Created Issues"
    elif action == "myclaimedissues_expand":
        data_key = 'myclaimedissues_data'
        delete_task_key = 'myclaimedissues_delete_task'
        title = "Your Claimed Issues"
    else:
        logger.error(f"Unknown action: {action}")
        return
    
    # Add status to expanded statuses
    myissues_data = context.user_data.get(data_key, {})
    expanded_statuses = myissues_data.get('expanded_statuses', set())
    expanded_statuses.add(status)
    myissues_data['expanded_statuses'] = expanded_statuses
    context.user_data[data_key] = myissues_data
    
    # Rebuild message
    issues_by_status = myissues_data.get('issues_by_status', {})
    total_issues = sum(len(issues) for issues in issues_by_status.values())
    chat_id = myissues_data.get('chat_id')
    user_id = myissues_data.get('user_id')
    username = myissues_data.get('username')
    message_text, keyboard = build_myissues_message(context, issues_by_status, total_issues, chat_id, user_id, username, title=title)
    
    # Update message
    try:
        await query.edit_message_text(
            text=message_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        logger.info(f"Expanded {status} issues for user {user_id} ({action})")
        
        # Cancel existing auto-delete task and reschedule
        if delete_task_key in context.user_data:
            old_task = context.user_data[delete_task_key]
            if not old_task.done():
                old_task.cancel()
                logger.info(f"Cancelled old auto-delete task")
        
        # Reschedule auto-delete after button click
        message_id = query.message.message_id
        
        async def delete_after_delay():
            await asyncio.sleep(40)
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=message_id
                )
                logger.info(f"Auto-deleted {action} message after 40 seconds (after button click)")
            except Exception as e:
                logger.warning(f"Failed to auto-delete {action} message: {e}")
        
        # Store new task
        context.user_data[delete_task_key] = asyncio.create_task(delete_after_delay())
        
    except Exception as e:
        logger.error(f"Error updating {action} message: {e}")
