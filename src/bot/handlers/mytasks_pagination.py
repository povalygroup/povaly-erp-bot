"""Pagination handler for /mytasks command."""

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def build_mytasks_message(context, tasks_by_state, total_tasks, chat_id, user_id=None, username=None):
    """Build the mytasks message with pagination."""
    message = "📋 **Your Tasks**\n\n"
    
    # Add user info at the top
    if user_id:
        message += f"👤 **User:** @{username or 'unknown'}\n"
        message += f"🆔 **ID:** {user_id}\n\n"
    
    # State order
    state_order = ['ASSIGNED', 'STARTED', 'QA_SUBMITTED', 'REJECTED', 'APPROVED']
    state_emojis = {
        'ASSIGNED': '📌',
        'STARTED': '⚙️',
        'QA_SUBMITTED': '🔍',
        'REJECTED': '❌',
        'APPROVED': '✅'
    }
    
    # Get config and pagination data
    config = context.bot_data.get('config')
    topic_id = config.TOPIC_TASK_ALLOCATION if config else None
    mytasks_data = context.user_data.get('mytasks_data', {})
    page_size = mytasks_data.get('page_size', 5)
    expanded_states = mytasks_data.get('expanded_states', set())
    
    # Build keyboard for "Show more" buttons
    keyboard_buttons = []
    
    for state in state_order:
        if state in tasks_by_state:
            tasks = tasks_by_state[state]
            emoji = state_emojis.get(state, '•')
            message += f"{emoji} **{state}** ({len(tasks)})\n"
            
            # Determine how many tasks to show
            if state in expanded_states:
                # Show all tasks
                tasks_to_show = tasks
            else:
                # Show only first page_size tasks
                tasks_to_show = tasks[:page_size]
            
            # Build links for tasks
            for task in tasks_to_show:
                # Create proper link format
                chat_id_str = str(chat_id)
                if chat_id_str.startswith('-100'):
                    group_id = chat_id_str[4:]
                else:
                    group_id = chat_id_str.lstrip('-')
                
                if topic_id:
                    link = f"https://t.me/c/{group_id}/{topic_id}/{task.message_id}"
                else:
                    link = f"https://t.me/c/{group_id}/{task.message_id}"
                
                # Check if task has blocking tasks (simplified - no await needed)
                # We'll show blocked indicator if task has blocking_tasks attribute set
                blocked_indicator = ""
                if hasattr(task, 'blocking_tasks') and task.blocking_tasks:
                    blocked_indicator = " 🚫"
                
                message += f"  • <a href='{link}'>#{task.ticket}</a> - {task.brand}{blocked_indicator}\n"
            
            # Add "Show more" button if there are more tasks
            if len(tasks) > page_size and state not in expanded_states:
                remaining = len(tasks) - page_size
                message += f"  • _... and {remaining} more_\n"
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"Show {remaining} more {state} tasks",
                        callback_data=f"mytasks_expand:{state}"
                    )
                ])
            
            message += "\n"
    
    message += f"**Total:** {total_tasks} tasks\n\n"
    message += "⏱️ _This task list will be deleted in 120 seconds..._"
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(keyboard_buttons) if keyboard_buttons else None
    
    return message, keyboard


async def handle_mytasks_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pagination button clicks for /mytasks."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    action, state = query.data.split(':', 1)
    
    if action == "mytasks_expand":
        # Add state to expanded states
        mytasks_data = context.user_data.get('mytasks_data', {})
        expanded_states = mytasks_data.get('expanded_states', set())
        expanded_states.add(state)
        mytasks_data['expanded_states'] = expanded_states
        context.user_data['mytasks_data'] = mytasks_data
        
        # Rebuild message
        tasks_by_state = mytasks_data.get('tasks_by_state', {})
        total_tasks = sum(len(tasks) for tasks in tasks_by_state.values())
        chat_id = mytasks_data.get('chat_id')
        user_id = mytasks_data.get('user_id')
        username = mytasks_data.get('username')
        message_text, keyboard = build_mytasks_message(context, tasks_by_state, total_tasks, chat_id, user_id, username)
        
        # Update message
        try:
            await query.edit_message_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            logger.info(f"Expanded {state} tasks for user {user_id}")
            
            # Cancel existing auto-delete task and reschedule
            if 'mytasks_delete_task' in context.user_data:
                old_task = context.user_data['mytasks_delete_task']
                if not old_task.done():
                    old_task.cancel()
                    logger.info(f"Cancelled old auto-delete task")
            
            # Reschedule auto-delete after button click
            message_id = query.message.message_id
            
            async def delete_after_delay():
                await asyncio.sleep(120)
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=message_id
                    )
                    logger.info(f"Auto-deleted /mytasks message after 120 seconds (after button click)")
                except Exception as e:
                    logger.warning(f"Failed to auto-delete /mytasks message: {e}")
            
            # Store new task
            context.user_data['mytasks_delete_task'] = asyncio.create_task(delete_after_delay())
            
        except Exception as e:
            logger.error(f"Error updating mytasks message: {e}")
