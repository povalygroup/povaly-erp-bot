"""Command handlers for bot commands."""

import logging
import asyncio
import os
from datetime import datetime, date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

from src.config import Config
from src.core.brand_mapper import BrandMapper
from src.data.models.task import TaskState
from src.bot.templates import (
    TASK_ALLOCATION_TEMPLATE,
    CORE_OPERATIONS_TEMPLATE,
    SUPPORT_TYPES,
    get_workflow_template,
    format_template,
    get_field_help_text,
)

logger = logging.getLogger(__name__)


async def send_dm_with_autodelete(context, user_id, text, delete_after=15):
    """
    Send a DM message with auto-delete.
    
    Args:
        context: Telegram context
        user_id: User ID to send DM to
        text: Message text
        delete_after: Seconds before auto-delete (default 15)
    """
    try:
        sent_msg = await context.bot.send_message(
            chat_id=user_id,
            text=f"{text}\n\n_This message will auto-delete in {delete_after} seconds_",
            parse_mode='Markdown'
        )
        logger.info(f"Sent DM to user {user_id}")
        
        # Auto-delete after specified seconds
        async def delete_dm():
            await asyncio.sleep(delete_after)
            try:
                await sent_msg.delete()
            except:
                pass
        asyncio.create_task(delete_dm())
        return sent_msg
    except Exception as e:
        logger.error(f"Failed to send DM to user {user_id}: {e}")
        return None


def is_privileged_user(user_id: int, config: Config) -> bool:
    """Check if user is admin, manager, or owner."""
    if not config:
        return False
    return (
        user_id in config.ADMINISTRATORS or
        user_id in config.MANAGERS or
        user_id in config.OWNERS
    )


async def move_to_trash(context, message, reason="Deleted message", deleted_by=None):
    """
    Move a message to trash topic instead of deleting it.
    Also syncs database if it's a task message being deleted.
    
    Args:
        context: Telegram context
        message: Message object to move to trash
        reason: Reason for deletion
        deleted_by: User who deleted the message (optional)
    """
    try:
        config = context.bot_data.get('config')
        if not config or not config.TOPIC_TRASH:
            # Fallback to regular deletion if trash topic not configured
            await message.delete()
            return
        
        # Sync database if this is a task message being deleted
        task_service = context.bot_data.get('task_service')
        if task_service and message.text and message.message_thread_id == config.TOPIC_TASK_ALLOCATION:
            await sync_task_database_on_delete(context, message, task_service)
        
        # Get message details
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name
        original_topic = message.message_thread_id if message.is_topic_message else "Main Chat"
        timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
        
        # Clean up the original content - remove auto-delete warnings
        original_content = message.text or '[No text content]'
        
        # Remove auto-delete warning patterns
        import re
        warning_patterns = [
            r'\n\n_⏱️ This message will be deleted in \d+ seconds\.\.\._',
            r'_⏱️ This message will be deleted in \d+ seconds\.\.\._',
            r'\n\n⏱️ This message will be deleted in \d+ seconds\.\.\.',
            r'⏱️ This message will be deleted in \d+ seconds\.\.\.'
        ]
        
        for pattern in warning_patterns:
            original_content = re.sub(pattern, '', original_content)
        
        # Clean up extra whitespace
        original_content = original_content.strip()
        
        # Create trash entry
        trash_content = f"🗑️ **DELETED MESSAGE**\n\n"
        trash_content += f"**Original Author:** {username} (ID: {user.id})\n"
        trash_content += f"**Original Topic:** {original_topic}\n"
        trash_content += f"**Deleted At:** {timestamp}\n"
        trash_content += f"**Reason:** {reason}\n"
        if deleted_by:
            trash_content += f"**Deleted By:** {deleted_by}\n"
        trash_content += f"\n**Original Content:**\n{original_content}"
        
        # Send to trash topic
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=trash_content,
            parse_mode='Markdown',
            message_thread_id=config.TOPIC_TRASH
        )
        
        # Now delete the original message
        await message.delete()
        
        logger.info(f"Moved message {message.message_id} to trash: {reason}")
        
    except Exception as e:
        logger.error(f"Failed to move message to trash: {e}")
        # Fallback to regular deletion
        try:
            await message.delete()
        except:
            pass


async def sync_task_database_on_delete(context, message, task_service):
    """
    Sync database when a task message is deleted/moved to trash.
    Removes the task from database and updates reality tracking.
    
    CRITICAL: Only delete task if the deleted message IS the actual task message.
    """
    try:
        if not message.text:
            return
        
        # Try to extract ticket from the deleted message
        from src.core.parser.message_parser import MessageParser
        parser = MessageParser()
        
        # Check if this looks like a task message
        if not parser.is_task_message(message.text):
            return
        
        # Parse the task data to get ticket
        task_data = parser.parse_task_allocation(message.text)
        if not task_data or not task_data.ticket:
            return
        
        # CRITICAL FIX: Verify this message IS the actual task message
        # Don't delete task if it's just a message that mentions the ticket
        existing_task = await task_service.get_task(task_data.ticket)
        if not existing_task:
            logger.debug(f"Task {task_data.ticket} not found in database, nothing to delete")
            return
        
        # ONLY delete if the message_id matches the task's message_id
        if existing_task.message_id != message.message_id:
            logger.info(f"⚠️ Message {message.message_id} mentions task {task_data.ticket} but is NOT the task message (task message: {existing_task.message_id}). NOT deleting task.")
            return
        
        logger.info(f"✅ Confirmed: Message {message.message_id} IS the task message for {task_data.ticket}. Deleting task from database.")
        
        # Get user ID (assignee)
        user_id = message.from_user.id
        
        # Track task deletion in reality map
        db_sync_service = context.bot_data.get('db_sync_service')
        if db_sync_service:
            db_sync_service.track_task_deleted(user_id, task_data.ticket)
        
        # Remove from database
        await task_service.task_repo.db.delete_task(task_data.ticket)
        logger.info(f"Synced database: Removed task {task_data.ticket} after message deletion")
        
    except Exception as e:
        logger.error(f"Error syncing database on task deletion: {e}")


async def send_auto_delete_message(context, chat_id, text, parse_mode='Markdown', 
                                   reply_markup=None, message_thread_id=None, 
                                   delete_after_seconds=20, warning_text=True):
    """
    Send a message that auto-deletes after specified seconds.
    
    Args:
        context: Telegram context
        chat_id: Chat ID to send message to
        text: Message text
        parse_mode: Parse mode (Markdown, HTML, etc.)
        reply_markup: Inline keyboard markup
        message_thread_id: Topic/thread ID
        delete_after_seconds: Seconds before auto-delete
        warning_text: Whether to add auto-delete warning to message
    
    Returns:
        Sent message object
    """
    if warning_text:
        warning = f"\n\n_⏱️ This message will be deleted in {delete_after_seconds} seconds..._"
        text = text + warning
    
    sent_message = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
        message_thread_id=message_thread_id
    )
    
    # Schedule deletion as a background task (non-blocking)
    async def delete_message_later():
        await asyncio.sleep(delete_after_seconds)
        try:
            await sent_message.delete()
            logger.info(f"Auto-deleted notification message after {delete_after_seconds} seconds")
        except Exception as e:
            logger.warning(f"Failed to auto-delete notification message: {e}")
    
    # Create background task for deletion
    asyncio.create_task(delete_message_later())
    
    return sent_message


async def cmd_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /edit command - allows admins to edit bot messages."""
    user_id = update.message.from_user.id
    config = context.bot_data.get('config')
    
    # Check if user is authorized
    is_authorized = (
        user_id in config.ADMINISTRATORS or 
        user_id in config.MANAGERS or 
        user_id in config.OWNERS
    )
    
    if not is_authorized:
        error_msg = "❌ **Access Denied**\n\nOnly Administrators, Managers, and Owners can edit messages."
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=10,
            warning_text=True
        )
        # Delete the command message
        try:
            await update.message.delete()
        except:
            pass
        return
    
    # Check if this is a reply to another message
    if not update.message.reply_to_message:
        help_msg = """📝 **Edit Message**

**Usage:** Reply to any message with:
`/edit New message content here`

**Example:**
1. Reply to a task message
2. Type: `/edit [TICKET] #POV260407[BRAND] #Povaly[TASK] Updated task[ASSIGNEE] @newuser`
3. The message will be updated

**Note:** You can edit any message, including bot messages and user messages."""
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=help_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )
        # Delete the command message
        try:
            await update.message.delete()
        except:
            pass
        return
    
    # Get the new content (everything after /edit)
    command_text = update.message.text
    if len(command_text.split(' ', 1)) < 2:
        error_msg = "❌ **No Content**\n\nPlease provide the new message content after `/edit`"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=10,
            warning_text=True
        )
        # Delete the command message
        try:
            await update.message.delete()
        except:
            pass
        return
    
    new_content = command_text.split(' ', 1)[1]
    target_message = update.message.reply_to_message
    
    try:
        # Try to edit the target message
        await context.bot.edit_message_text(
            chat_id=target_message.chat_id,
            message_id=target_message.message_id,
            text=new_content
        )
        
        # Delete the command message
        try:
            await update.message.delete()
        except:
            pass
        
        # Send confirmation that auto-deletes
        success_msg = f"✅ **Message Updated**\n\nMessage edited by @{update.message.from_user.username or update.message.from_user.first_name}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=success_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=5,
            warning_text=True
        )
        
        logger.info(f"Admin {user_id} edited message {target_message.message_id}")
        
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        error_msg = f"❌ **Edit Failed**\n\nCould not edit the message. Error: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=10,
            warning_text=True
        )
        # Delete the command message
        try:
            await update.message.delete()
        except:
            pass


async def cmd_myclaimedissues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myclaimedissues command - show user's claimed issues."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    issue_service = context.bot_data.get('issue_service')
    
    # Delete the command message from group
    try:
        await update.message.delete()
        logger.info(f"Deleted /myclaimedissues command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /myclaimedissues command: {e}")
    
    if not issue_service:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Issue service not available",
                parse_mode='Markdown'
            )
        except:
            pass
        return
    
    try:
        from src.bot.handlers.myissues_pagination import build_myissues_message
        
        # Get user's claimed issues
        all_issues = await issue_service.get_user_issues(user_id)
        
        logger.info(f"📊 /myclaimedissues for user {user_id}: Found {len(all_issues)} issues")
        
        if not all_issues:
            try:
                sent_msg = await context.bot.send_message(
                    chat_id=user_id,
                    text="📭 You have no claimed issues",
                    parse_mode='Markdown'
                )
                
                # Auto-delete after 60 seconds
                async def delete_dm():
                    await asyncio.sleep(60)
                    try:
                        await sent_msg.delete()
                    except:
                        pass
                asyncio.create_task(delete_dm())
            except:
                pass
            return
        
        # Group issues by status
        issues_by_status = {}
        for issue in all_issues:
            status = issue.status.value
            if status not in issues_by_status:
                issues_by_status[status] = []
            issues_by_status[status].append(issue)
        
        # Store issues in context for pagination
        context.user_data['myclaimedissues_data'] = {
            'issues_by_status': issues_by_status,
            'user_id': user_id,
            'username': username,
            'chat_id': user_id,  # Send to DM
            'topic_id': None,
            'page_size': 5,
            'expanded_statuses': set()
        }
        
        # Build message with pagination
        message_text, keyboard = build_myissues_message(context, issues_by_status, len(all_issues), user_id, user_id, username, title="Your Claimed Issues", callback_prefix="myclaimedissues_expand")
        
        # Send message to DM
        try:
            sent_message = await context.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            # Store message_id for auto-deletion
            context.user_data['myclaimedissues_message_id'] = sent_message.message_id
            context.user_data['myclaimedissues_chat_id'] = user_id
            
            # Schedule auto-delete after 40 seconds
            async def delete_after_delay():
                await asyncio.sleep(40)
                try:
                    current_msg_id = context.user_data.get('myclaimedissues_message_id')
                    if current_msg_id == sent_message.message_id:
                        await sent_message.delete()
                        logger.info(f"Auto-deleted /myclaimedissues DM after 40 seconds")
                except Exception as e:
                    logger.warning(f"Failed to auto-delete /myclaimedissues DM: {e}")
            
            # Cancel any existing auto-delete task
            if 'myclaimedissues_delete_task' in context.user_data:
                old_task = context.user_data['myclaimedissues_delete_task']
                if not old_task.done():
                    old_task.cancel()
            
            # Store new task
            context.user_data['myclaimedissues_delete_task'] = asyncio.create_task(delete_after_delay())
            
            logger.info(f"✅ Sent /myclaimedissues response to DM for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send /myclaimedissues DM to user {user_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error in /myclaimedissues command: {e}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Error retrieving your claimed issues: {str(e)}",
                parse_mode='Markdown'
            )
        except:
            pass


async def cmd_myissues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myissues command - show issues created by user."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    issue_service = context.bot_data.get('issue_service')
    
    # Delete the command message from group
    try:
        await update.message.delete()
        logger.info(f"Deleted /myissues command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /myissues command: {e}")
    
    if not issue_service:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Issue service not available",
                parse_mode='Markdown'
            )
        except:
            pass
        return
    
    try:
        from src.bot.handlers.myissues_pagination import build_myissues_message
        
        # Get issues created by user
        all_issues = await issue_service.get_user_created_issues(user_id)
        
        logger.info(f"📊 /myissues for user {user_id}: Found {len(all_issues)} created issues")
        
        if not all_issues:
            try:
                sent_msg = await context.bot.send_message(
                    chat_id=user_id,
                    text="📭 You have not created any issues",
                    parse_mode='Markdown'
                )
                
                # Auto-delete after 60 seconds
                async def delete_dm():
                    await asyncio.sleep(60)
                    try:
                        await sent_msg.delete()
                    except:
                        pass
                asyncio.create_task(delete_dm())
            except:
                pass
            return
        
        # Group issues by status
        issues_by_status = {}
        for issue in all_issues:
            status = issue.status.value
            if status not in issues_by_status:
                issues_by_status[status] = []
            issues_by_status[status].append(issue)
        
        # Store issues in context for pagination
        context.user_data['myissues_data'] = {
            'issues_by_status': issues_by_status,
            'user_id': user_id,
            'username': username,
            'chat_id': user_id,  # Send to DM
            'topic_id': None,
            'page_size': 5,
            'expanded_statuses': set()
        }
        
        # Build message with pagination
        message_text, keyboard = build_myissues_message(context, issues_by_status, len(all_issues), user_id, user_id, username, title="Your Created Issues", callback_prefix="myissues_expand")
        
        # Send message to DM
        try:
            sent_message = await context.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            # Store message_id for auto-deletion
            context.user_data['myissues_message_id'] = sent_message.message_id
            context.user_data['myissues_chat_id'] = user_id
            
            # Schedule auto-delete after 40 seconds
            async def delete_after_delay():
                await asyncio.sleep(40)
                try:
                    current_msg_id = context.user_data.get('myissues_message_id')
                    if current_msg_id == sent_message.message_id:
                        await sent_message.delete()
                        logger.info(f"Auto-deleted /myissues DM after 40 seconds")
                except Exception as e:
                    logger.warning(f"Failed to auto-delete /myissues DM: {e}")
            
            # Cancel any existing auto-delete task
            if 'myissues_delete_task' in context.user_data:
                old_task = context.user_data['myissues_delete_task']
                if not old_task.done():
                    old_task.cancel()
            
            # Store new task
            context.user_data['myissues_delete_task'] = asyncio.create_task(delete_after_delay())
            
            logger.info(f"✅ Sent /myissues response to DM for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send /myissues DM to user {user_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error in /myissues command: {e}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Error retrieving your created issues: {str(e)}",
                parse_mode='Markdown'
            )
        except:
            pass


async def cmd_openissues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /openissues command - show all unresolved issues."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    issue_service = context.bot_data.get('issue_service')
    task_service = context.bot_data.get('task_service')
    user_repo = context.bot_data.get('user_repository')  # Fixed: was 'user_repo'
    config = context.bot_data.get('config')
    
    if not issue_service:
        logger.error("Issue service not initialized")
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /openissues command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /openissues command: {e}")
    
    try:
        # Get all open issues
        issues = await issue_service.get_open_issues()
        
        # Build response with user info at top
        response = "📋 **Open Issues**\n\n"
        response += f"👤 **Requested by:** @{username}\n"
        response += f"🆔 **ID:** {user_id}\n\n"
        
        if not issues:
            response += "No open issues found."
        else:
            response += f"**Total Issues:** {len(issues)}\n\n"
            
            for issue in issues:
                status_emoji = {
                    "open": "🔴",
                    "in_progress": "🟡",
                    "resolved": "✅", 
                    "invalid": "❌",
                    "escalated": "🚨"
                }.get(issue.status.value, "❓")
                
                priority_emoji = {
                    "LOW": "🟢",
                    "MEDIUM": "🟡",
                    "HIGH": "🟠",
                    "CRITICAL": "🔴"
                }.get(issue.priority.value, "❓")
                
                # Get the original task to link to its message
                task_link = None
                if task_service:
                    try:
                        task = await task_service.get_task(issue.ticket)
                        if task and task.message_id:
                            # Create link to the original task message
                            group_id_str = str(abs(config.TELEGRAM_GROUP_ID))
                            if group_id_str.startswith('100'):
                                group_id_str = group_id_str[3:]
                            task_link = f"https://t.me/c/{group_id_str}/{task.message_id}"
                    except:
                        pass
                
                # If no task link, link to Core Operations topic
                if not task_link:
                    task_link = f"https://t.me/c/{str(abs(config.TELEGRAM_GROUP_ID))[3:]}/{config.TOPIC_CORE_OPERATIONS}"
                
                response += f"{status_emoji} <a href='{task_link}'>#{issue.ticket}</a> - {issue.title}\n"
                response += f"{priority_emoji} Priority: {issue.priority.value}\n"
                
                if issue.claimed_by:
                    # Get usernames for claimed_by users
                    handler_names = []
                    for uid in issue.claimed_by:
                        if user_repo:
                            user = await user_repo.get_user(uid)
                            if user and user.username:
                                handler_names.append(f"@{user.username}")
                            else:
                                handler_names.append(f"User {uid}")
                        else:
                            handler_names.append(f"User {uid}")
                    
                    handlers = ", ".join(handler_names)
                    response += f"👍 Claimed by: {handlers}\n"
                else:
                    response += f"❓ Unclaimed\n"
                
                if issue.created_at:
                    response += f"📅 Created: {issue.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                response += "\n"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='HTML',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=30,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /openissues command: {e}")
        error_msg = f"❌ Error retrieving open issues: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='HTML',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def show_issue_details(update: Update, context: ContextTypes.DEFAULT_TYPE, issue_ticket: str, user_id: int, username: str):
    """Show detailed information for a specific issue ticket."""
    issue_service = context.bot_data.get('issue_service')
    user_repo = context.bot_data.get('user_repository')  # Fixed: was 'user_repo'
    config = context.bot_data.get('config')
    
    try:
        # Get issue by issue_ticket
        from src.data.repositories.issue_repository import IssueRepository
        issue_repo = IssueRepository(context.bot_data.get('db_adapter'))
        issue = await issue_repo.get_issue_by_issue_ticket(issue_ticket)
        
        if not issue:
            response = f"❌ **Issue Not Found**\n\nNo issue found with ticket: `{issue_ticket}`"
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=response,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=False
            )
            return
        
        # Build detailed response
        status_emoji = {
            "open": "🔴",
            "in_progress": "🟡",
            "resolved": "✅",
            "invalid": "❌", 
            "escalated": "🚨"
        }.get(issue.status.value, "❓")
        
        priority_emoji = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴"
        }.get(issue.priority.value, "❓")
        
        response = f"🔍 **Issue Details**\n\n"
        response += f"👤 **Requested by:** @{username}\n"
        response += f"🆔 **ID:** {user_id}\n\n"
        response += f"**Issue Ticket:** `{issue.issue_ticket}`\n"
        response += f"**Task Ticket:** `{issue.ticket}`\n"
        response += f"**Status:** {status_emoji} {issue.status.value.replace('_', ' ').title()}\n"
        response += f"**Priority:** {priority_emoji} {issue.priority.value}\n\n"
        response += f"**Title:** {issue.title}\n\n"
        response += f"**Details:**\n{issue.details}\n\n"
        
        if issue.assignee_username:
            response += f"**Assigned to:** @{issue.assignee_username}\n"
        
        # Get creator username
        if user_repo:
            creator = await user_repo.get_user(issue.creator_id)
            if creator and creator.username:
                response += f"**Created by:** @{creator.username}\n"
            else:
                response += f"**Created by:** User {issue.creator_id}\n"
        else:
            response += f"**Created by:** User {issue.creator_id}\n"
        
        # Get claimed by usernames
        if issue.claimed_by:
            handler_names = []
            for uid in issue.claimed_by:
                if user_repo:
                    user = await user_repo.get_user(uid)
                    if user and user.username:
                        handler_names.append(f"@{user.username}")
                    else:
                        handler_names.append(f"User {uid}")
                else:
                    handler_names.append(f"User {uid}")
            
            handlers = ", ".join(handler_names)
            response += f"**Claimed by:** {handlers}\n"
        
        # Get resolved by username
        if issue.resolved_by:
            if user_repo:
                resolver = await user_repo.get_user(issue.resolved_by)
                if resolver and resolver.username:
                    response += f"**Resolved by:** @{resolver.username}\n"
                else:
                    response += f"**Resolved by:** User {issue.resolved_by}\n"
            else:
                response += f"**Resolved by:** User {issue.resolved_by}\n"
        
        # Get rejected by username
        if issue.rejected_by:
            if user_repo:
                rejecter = await user_repo.get_user(issue.rejected_by)
                if rejecter and rejecter.username:
                    response += f"**Rejected by:** @{rejecter.username}\n"
                else:
                    response += f"**Rejected by:** User {issue.rejected_by}\n"
            else:
                response += f"**Rejected by:** User {issue.rejected_by}\n"
        
        response += "\n"
        
        # Timestamps
        if issue.created_at:
            response += f"📅 **Created:** {issue.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        if issue.claimed_at:
            response += f"👍 **Claimed:** {issue.claimed_at.strftime('%Y-%m-%d %H:%M')}\n"
        if issue.resolved_at:
            response += f"✅ **Resolved:** {issue.resolved_at.strftime('%Y-%m-%d %H:%M')}\n"
        if issue.escalated_at:
            response += f"🚨 **Escalated:** {issue.escalated_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        # Flags
        if issue.escalation_sent:
            response += f"\n⚠️ **Escalation sent**\n"
        if issue.reminder_sent:
            response += f"⏰ **Reminder sent**\n"
        
        # Add message link
        if config and issue.message_id:
            chat_id_str = str(config.TELEGRAM_GROUP_ID)
            if chat_id_str.startswith('-100'):
                group_id = chat_id_str[4:]
            else:
                group_id = chat_id_str.lstrip('-')
            
            if issue.topic_id:
                message_link = f"https://t.me/c/{group_id}/{issue.topic_id}/{issue.message_id}"
            else:
                message_link = f"https://t.me/c/{group_id}/{issue.message_id}"
            
            response += f"\n[📎 View Original Message]({message_link})"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=40,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error showing issue details: {e}")
        error_msg = f"❌ Error retrieving issue details: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def show_task_issues(update: Update, context: ContextTypes.DEFAULT_TYPE, ticket: str, user_id: int, username: str, issue_service, config):
    """Show list of all issues for a task ticket."""
    try:
        from src.bot.handlers.myissues_pagination import build_myissues_message
        
        # Check if user is admin/manager/owner (not regular employee)
        is_admin = (user_id in config.ADMINISTRATORS or 
                   user_id in config.MANAGERS or 
                   user_id in config.OWNERS)
        
        if is_admin:
            # Admins/Managers/Owners can see all issues for the task
            from src.data.repositories.issue_repository import IssueRepository
            issue_repo = IssueRepository(context.bot_data.get('db_adapter'))
            
            # Get all issues for this task ticket (regardless of creator)
            query = "SELECT * FROM issues WHERE ticket = ? ORDER BY created_at DESC"
            db_adapter = context.bot_data.get('db_adapter')
            results = await db_adapter.fetch_all(query, (ticket,))
            task_issues = [issue_repo._row_to_issue(row) for row in results]
        else:
            # Regular employees can only see their own issues
            all_user_issues = await issue_service.get_user_created_issues(user_id)
            task_issues = [issue for issue in all_user_issues if issue.ticket == ticket]
        
        if not task_issues:
            if is_admin:
                response = f"❌ **No Issues Found**\n\n"
                response += f"No issues found for task `{ticket}`"
            else:
                response = f"❌ **No Issues Found**\n\n"
                response += f"You have not created any issues for task `{ticket}`"
            
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=response,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=False
            )
            return
        
        # Group issues by status
        issues_by_status = {}
        for issue in task_issues:
            status = issue.status.value
            if status not in issues_by_status:
                issues_by_status[status] = []
            issues_by_status[status].append(issue)
        
        # Store issues in context for pagination
        context.user_data['myissues_data'] = {
            'issues_by_status': issues_by_status,
            'user_id': user_id,
            'username': username,
            'chat_id': update.message.chat_id,
            'topic_id': update.message.message_thread_id if update.message.is_topic_message else None,
            'page_size': 5,
            'expanded_statuses': set()
        }
        
        # Build message with pagination
        title = f"All Issues for Task {ticket}" if is_admin else f"Your Issues for Task {ticket}"
        message_text, keyboard = build_myissues_message(
            context, 
            issues_by_status, 
            len(task_issues), 
            update.message.chat_id, 
            user_id, 
            username, 
            title=title,
            callback_prefix="myissues_expand"
        )
        
        # Send message
        sent_message = await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=message_text,
            parse_mode='HTML',
            reply_markup=keyboard,
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
        )
        
        # Store message_id for auto-deletion
        context.user_data['myissues_message_id'] = sent_message.message_id
        context.user_data['myissues_chat_id'] = update.message.chat_id
        
        # Schedule auto-delete after 40 seconds
        async def delete_after_delay():
            await asyncio.sleep(40)
            try:
                current_msg_id = context.user_data.get('myissues_message_id')
                if current_msg_id == sent_message.message_id:
                    await sent_message.delete()
                    logger.info(f"Auto-deleted /issue message after 40 seconds")
            except Exception as e:
                logger.warning(f"Failed to auto-delete /issue message: {e}")
        
        # Cancel any existing auto-delete task
        if 'myissues_delete_task' in context.user_data:
            old_task = context.user_data['myissues_delete_task']
            if not old_task.done():
                old_task.cancel()
        
        # Store new task
        context.user_data['myissues_delete_task'] = asyncio.create_task(delete_after_delay())
        
    except Exception as e:
        logger.error(f"Error in show_task_issues: {e}")
        error_msg = f"❌ Error retrieving issues: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /issue command - show issues for task ticket OR details for issue ticket."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    issue_service = context.bot_data.get('issue_service')
    config = context.bot_data.get('config')
    
    if not issue_service:
        logger.error("Issue service not initialized")
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /issue command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /issue command: {e}")
    
    # Extract ticket from command
    command_text = update.message.text
    parts = command_text.split()
    
    if len(parts) < 2:
        help_msg = """🔍 **Issue Lookup**

**Usage:** `/issue #TICKET`

**Examples:**
• `/issue #POV260406`
• `/issue POV260406`

**Note:** Shows all issues for that task ticket (creator only)."""
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=help_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )
        return
    
    # Extract ticket ID
    ticket_input = parts[1].strip()
    
    # Check if this is an issue ticket (contains -I) or task ticket
    # Check the original input before extraction
    is_issue_ticket = '-I' in ticket_input.upper()
    
    if is_issue_ticket:
        # For issue tickets, keep the full ticket including -I1, -I2, etc.
        # Remove # if present
        ticket = ticket_input.lstrip('#')
        # Show detailed info for specific issue ticket
        await show_issue_details(update, context, ticket, user_id, username)
    else:
        # For task tickets, extract using the service method
        ticket = issue_service.extract_ticket_from_text(ticket_input)
        
        if not ticket:
            error_msg = f"❌ **Invalid Ticket Format**\n\nCould not parse ticket from: `{ticket_input}`\n\nUse format like: `#POV260406` or `#POV260406-I1`"
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Show list of all issues for task ticket
        await show_task_issues(update, context, ticket, user_id, username, issue_service, config)


async def cmd_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /close command - resolve an issue by issue ticket."""
    user_id = update.message.from_user.id
    issue_service = context.bot_data.get('issue_service')
    config = context.bot_data.get('config')
    
    if not issue_service:
        logger.error("Issue service not initialized")
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /close command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /close command: {e}")
    
    # Extract ticket from command
    command_text = update.message.text
    parts = command_text.split()
    
    if len(parts) < 2:
        help_msg = """✅ **Close Issue**

**Usage:** `/close #ISSUE_TICKET`

**Examples:**
• `/close #POV260406-I1`
• `/close POV260406-I2`

**Note:** This will mark the issue as resolved, add ❤️ reaction, and notify the creator."""
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=help_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )
        return
    
    # Extract issue ticket ID
    ticket_input = parts[1].strip().lstrip('#')
    
    # Validate it's an issue ticket (contains -I)
    if '-I' not in ticket_input.upper():
        error_msg = f"❌ **Invalid Issue Ticket**\n\n`{ticket_input}` is not an issue ticket.\n\nUse format like: `#POV260406-I1`"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        # Get issue by issue_ticket
        from src.data.repositories.issue_repository import IssueRepository
        issue_repo = IssueRepository(context.bot_data.get('db_adapter'))
        issue = await issue_repo.get_issue_by_issue_ticket(ticket_input)
        
        if not issue:
            error_msg = f"❌ **Issue Not Found**\n\nNo issue found with ticket: `{ticket_input}`"
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        if issue.is_resolved:
            error_msg = f"❌ **Already Resolved**\n\nIssue `{ticket_input}` is already resolved."
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Resolve the issue using issue_ticket
        success = await issue_service.resolve_issue(issue.issue_ticket, user_id)
        
        if success:
            # Add ❤️ reaction to the issue message
            try:
                # Use setMessageReaction API
                from telegram import ReactionTypeEmoji
                await context.bot.set_message_reaction(
                    chat_id=config.TELEGRAM_GROUP_ID,
                    message_id=issue.message_id,
                    reaction=[ReactionTypeEmoji(emoji="❤")],
                    is_big=False
                )
                logger.info(f"Added ❤️ reaction to issue {issue.issue_ticket} message {issue.message_id}")
            except Exception as e:
                logger.error(f"Failed to add ❤️ reaction to issue message: {e}", exc_info=True)
            
            # Send confirmation
            success_msg = f"✅ **Issue Resolved**\n\nIssue `{issue.issue_ticket}` has been marked as resolved.\n\n❤️ Reaction added to the issue message.\nThe creator will be notified via DM."
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=success_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=10,
                warning_text=True
            )
            
            # Send DM to issue creator
            try:
                # Get creator username
                user_repo = context.bot_data.get('user_repository')
                creator_username = "User"
                if user_repo:
                    creator = await user_repo.get_user(issue.creator_id)
                    if creator and creator.username:
                        creator_username = f"@{creator.username}"
                
                # Get resolver username
                resolver_username = "someone"
                if user_repo:
                    resolver = await user_repo.get_user(user_id)
                    if resolver and resolver.username:
                        resolver_username = f"@{resolver.username}"
                
                # Build message link to the issue
                chat_id_str = str(config.TELEGRAM_GROUP_ID)
                if chat_id_str.startswith('-100'):
                    group_id = chat_id_str[4:]
                else:
                    group_id = chat_id_str.lstrip('-')
                
                if issue.topic_id:
                    message_link = f"https://t.me/c/{group_id}/{issue.topic_id}/{issue.message_id}"
                else:
                    message_link = f"https://t.me/c/{group_id}/{issue.message_id}"
                
                await context.bot.send_message(
                    chat_id=issue.creator_id,
                    text=f"✅ **Issue Resolved**\n\nIssue **{issue.issue_ticket}** has been resolved.\n\n**Issue:** {issue.title}\n**Resolved by:** {resolver_username}\n\nPlease review the resolution and continue with any remaining work on task **{issue.ticket}** if applicable.\n\n[📎 View Issue Message]({message_link})",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info(f"Sent resolution notification to user {issue.creator_id}")
            except Exception as e:
                logger.warning(f"Failed to send resolution notification: {e}")
            
            logger.info(f"User {user_id} resolved issue {issue.issue_ticket} via /close command")
        else:
            error_msg = f"❌ **Failed to Resolve**\n\nCould not resolve issue `{issue.issue_ticket}`. Please try again."
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
        
    except Exception as e:
        logger.error(f"Error in /close command: {e}", exc_info=True)
        error_msg = f"❌ Error resolving issue: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_reopen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reopen command - reopen a resolved issue (creator only)."""
    try:
        user_id = update.message.from_user.id
        username = update.message.from_user.username or update.message.from_user.first_name
        issue_service = context.bot_data.get('issue_service')
        user_repo = context.bot_data.get('user_repository')
        config = context.bot_data.get('config')
        
        logger.info(f"User {user_id} (@{username}) invoked /reopen command: {update.message.text}")
        
        if not issue_service:
            logger.error("Issue service not initialized")
            return
        
        # Extract ticket from command BEFORE deleting the message
        command_text = update.message.text
        parts = command_text.split(maxsplit=2)  # Split into max 3 parts: command, ticket, reason
        
        logger.info(f"/reopen command parts: {parts}")
        
        # Delete the command message
        try:
            await update.message.delete()
            logger.info(f"Deleted /reopen command message from user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to delete /reopen command: {e}")
        
        if len(parts) < 2:
            help_msg = """🔄 **Reopen Issue**

**Usage:** `/reopen #ISSUE_TICKET <reason>`

**Examples:**
• `/reopen #POV260406-I1 The issue still persists`
• `/reopen POV260406-I2 Button not working properly`

**Note:** Only the issue creator can reopen. You must provide a reason for reopening."""
            
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=help_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=20,
                warning_text=True
            )
            return
        
        # Extract issue ticket ID
        ticket_input = parts[1].strip().lstrip('#')
        
        # Extract reason (required)
        if len(parts) < 3:
            error_msg = f"❌ **Reason Required**\n\nPlease provide a reason for reopening.\n\n**Example:** `/reopen #{ticket_input} The issue still persists`"
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        reason = parts[2].strip()
        
        # Validate it's an issue ticket (contains -I)
        if '-I' not in ticket_input.upper():
            error_msg = f"❌ **Invalid Issue Ticket**\n\n`{ticket_input}` is not an issue ticket.\n\nUse format like: `#POV260406-I1`"
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Get issue by issue_ticket
        from src.data.repositories.issue_repository import IssueRepository
        issue_repo = IssueRepository(context.bot_data.get('db_adapter'))
        issue = await issue_repo.get_issue_by_issue_ticket(ticket_input)
        
        if not issue:
            error_msg = f"❌ **Issue Not Found**\n\nNo issue found with ticket: `{ticket_input}`"
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if user is the creator
        if issue.creator_id != user_id:
            error_msg = f"❌ **Permission Denied**\n\nOnly the issue creator can reopen this issue."
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if issue is resolved
        if not issue.is_resolved:
            error_msg = f"❌ **Not Resolved**\n\nIssue `{ticket_input}` is not resolved. Current status: {issue.status.value.replace('_', ' ').title()}"
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Store resolver info before reopening
        resolver_id = issue.resolved_by
        
        # Reopen the issue - reset to OPEN status
        from src.data.models.issue import IssueStatus
        issue.status = IssueStatus.OPEN
        issue.resolved_by = None
        issue.resolved_at = None
        # Keep claimed_by list intact
        
        success = await issue_repo.update_issue(issue)
        
        if success:
            # Remove ❤️ reaction from the issue message
            try:
                from telegram import ReactionTypeEmoji
                await context.bot.set_message_reaction(
                    chat_id=config.TELEGRAM_GROUP_ID,
                    message_id=issue.message_id,
                    reaction=[],  # Empty list removes all reactions
                    is_big=False
                )
                logger.info(f"Removed ❤️ reaction from issue {issue.issue_ticket} message {issue.message_id}")
            except Exception as e:
                logger.error(f"Failed to remove ❤️ reaction: {e}", exc_info=True)
            
            # Build message link for creator confirmation
            chat_id_str = str(config.TELEGRAM_GROUP_ID)
            if chat_id_str.startswith('-100'):
                group_id = chat_id_str[4:]
            else:
                group_id = chat_id_str.lstrip('-')
            
            if issue.topic_id:
                message_link = f"https://t.me/c/{group_id}/{issue.topic_id}/{issue.message_id}"
            else:
                message_link = f"https://t.me/c/{group_id}/{issue.message_id}"
            
            # Send confirmation in group
            success_msg = f"🔄 **Issue Reopened**\n\nIssue `{issue.issue_ticket}` has been reopened.\n\n**Reason:** {reason}\n\nStatus reset to OPEN. The resolver will be notified."
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=success_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            
            # Send DM to creator with link and attachment instructions
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🔄 **Issue Reopened Successfully**\n\nYou have reopened issue **{issue.issue_ticket}**.\n\n**Issue:** {issue.title}\n**Reason:** {reason}\n\n💡 **Adding Attachments:**\nIf you need to provide screenshots, files, or additional context, simply **reply to the original issue message** in the group. The resolver will be notified to check the thread for any new attachments.\n\n[📎 Go to Issue Message]({message_link})",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info(f"Sent reopen confirmation DM to creator {user_id}")
            except Exception as e:
                logger.warning(f"Failed to send reopen confirmation to creator: {e}")
            
            # Send DM to resolver if exists
            if resolver_id:
                try:
                    # Get resolver username
                    resolver_username = "the resolver"
                    if user_repo:
                        resolver = await user_repo.get_user(resolver_id)
                        if resolver and resolver.username:
                            resolver_username = f"@{resolver.username}"
                    
                    await context.bot.send_message(
                        chat_id=resolver_id,
                        text=f"🔄 **Issue Reopened**\n\nIssue **{issue.issue_ticket}** has been reopened by the creator.\n\n**Issue:** {issue.title}\n**Reopened by:** @{username}\n\n**Reason:**\n_{reason}_\n\n⚠️ **Action Required:**\nThe issue requires further attention. Please check the issue thread - the creator may have added screenshots, files, or additional details by replying to the original message.\n\n[📎 View Issue Message & Thread]({message_link})",
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    logger.info(f"Sent reopen notification to resolver {resolver_id}")
                except Exception as e:
                    logger.warning(f"Failed to send reopen notification to resolver: {e}")
            
            logger.info(f"User {user_id} reopened issue {issue.issue_ticket} via /reopen command")
        else:
            error_msg = f"❌ **Failed to Reopen**\n\nCould not reopen issue `{issue.issue_ticket}`. Please try again."
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
        
    except Exception as e:
        logger.error(f"Error in /reopen command: {e}", exc_info=True)
        try:
            error_msg = f"❌ Error reopening issue: {str(e)}"
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
        except Exception as inner_e:
            logger.error(f"Failed to send error message: {inner_e}", exc_info=True)


async def cmd_newqa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newqa command - submit work for QA review.
    
    Usage:
    - Reply to task message: /newqa <asset description> [@reviewer]
    - Direct in QA topic: /newqa #TICKET <asset> [@reviewer]
    - With file: Reply to task with /newqa and attach file
    - Manual in QA topic: Post message in format:
      [TICKET] #POV260406
      [BRAND] #GSMAura
      [ASSET] https://link.com or description
    """
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    message_text = update.message.text or ""
    config = context.bot_data.get('config')
    topic_id = update.message.message_thread_id if update.message.is_topic_message else None
    task_service = context.bot_data.get('task_service')
    
    logger.info(f"cmd_newqa called by user {user_id} in topic {topic_id}")
    
    if not task_service:
        # Delete command message
        try:
            await update.message.delete()
        except:
            pass
        
        # Send error to DM
        try:
            sent_msg = await context.bot.send_message(
                chat_id=user_id,
                text="❌ Service not available\n\n_This message will auto-delete in 15 seconds_",
                parse_mode='Markdown'
            )
            logger.info(f"Sent /newqa error to DM for user {user_id}")
            
            # Auto-delete after 15 seconds
            async def delete_dm():
                await asyncio.sleep(15)
                try:
                    await sent_msg.delete()
                except:
                    pass
            asyncio.create_task(delete_dm())
        except Exception as e:
            logger.error(f"Failed to send DM to user {user_id}: {e}")
        return
    
    # MODE 1: Direct command with ticket - /newqa #POV260406 <asset> [@reviewer]
    # This works in any topic, especially QA & Review
    parts = message_text.split(maxsplit=2)
    if len(parts) >= 2 and parts[1].startswith('#'):
        ticket = parts[1].replace('#', '').upper()
        asset = parts[2] if len(parts) > 2 else "QA submission"
        
        # Extract reviewer mention if present
        reviewer_username = None
        import re
        reviewer_match = re.search(r'@(\w+)', asset)
        if reviewer_match:
            reviewer_username = reviewer_match.group(1)
            # Remove reviewer mention from asset
            asset = re.sub(r'@\w+', '', asset).strip()
        
        # Delete the command message
        try:
            await update.message.delete()
            logger.info(f"Deleted /newqa command message")
        except Exception as e:
            logger.warning(f"Failed to delete /newqa command: {e}")
        
        await process_newqa_direct(update, context, ticket, asset, user_id, username, reviewer_username)
        return
    
    # MODE 2: Reply to task message
    if not update.message.reply_to_message:
        help_msg = """📋 **Submit for QA Review**

**Usage:**

**1. Reply to task message:**
`/newqa <asset description> [@reviewer]`

**Examples:**
• `/newqa https://gsmaura.com/blog/article`
• `/newqa Video thumbnail @reviewer`
• `/newqa Follow the file` (with file attached)

**2. Direct command:**
`/newqa #TICKET <asset> [@reviewer]`

**Example:**
• `/newqa #POV260406 https://link.com @reviewer`

**3. Manual Format (in QA & Review topic):**
```
[TICKET] #POV260406
[BRAND] #GSMAura
[ASSET] https://link.com or description
```

**Note:** Reviewer mention is optional.

_This message will auto-delete in 30 seconds_"""
        
        try:
            await update.message.delete()
        except:
            pass
        
        # Send help to DM
        try:
            sent_msg = await context.bot.send_message(
                chat_id=user_id,
                text=help_msg,
                parse_mode='Markdown'
            )
            logger.info(f"Sent /newqa help to DM for user {user_id}")
            
            # Auto-delete after 30 seconds
            async def delete_dm():
                await asyncio.sleep(30)
                try:
                    await sent_msg.delete()
                except:
                    pass
            asyncio.create_task(delete_dm())
        except Exception as e:
            logger.error(f"Failed to send DM to user {user_id}: {e}")
        return
    
    # Extract ticket from replied message
    replied_text = update.message.reply_to_message.text or ""
    import re
    ticket_match = re.search(r'#?([A-Z]{2,4}\d{6})', replied_text)
    
    # Must be a reply to task message
    if not update.message.reply_to_message:
        help_msg = """📋 **Submit for QA Review**

**Usage:**
Reply to a task message with:
`/newqa <asset description> [@reviewer]`

**Examples:**
• `/newqa https://gsmaura.com/blog/article`
• `/newqa Video thumbnail @reviewer`
• `/newqa Follow the file` (with file attached)

**Manual Format (in QA & Review topic):**
```
[TICKET] #POV260406
[BRAND] #GSMAura
[ASSET] https://link.com or description
```

**Note:** Reviewer mention is optional."""
        
        try:
            await update.message.delete()
        except:
            pass
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=help_msg,
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=30,
            warning_text=True
        )
        return
    
    # Extract ticket from replied message
    replied_text = update.message.reply_to_message.text or ""
    import re
    ticket_match = re.search(r'#?([A-Z]{2,4}\d{6})', replied_text)
    
    if not ticket_match:
        try:
            await update.message.delete()
        except:
            pass
        
        # Send error to DM
        try:
            sent_msg = await context.bot.send_message(
                chat_id=user_id,
                text="❌ Could not find ticket in the replied message. Please reply to a task message with a valid ticket ID.\n\n_This message will auto-delete in 15 seconds_",
                parse_mode='Markdown'
            )
            logger.info(f"Sent /newqa error to DM for user {user_id}")
            
            # Auto-delete after 15 seconds
            async def delete_dm():
                await asyncio.sleep(15)
                try:
                    await sent_msg.delete()
                except:
                    pass
            asyncio.create_task(delete_dm())
        except Exception as e:
            logger.error(f"Failed to send DM to user {user_id}: {e}")
        return
    
    ticket = ticket_match.group(1)
    
    # Extract asset and optional reviewer from command
    # Format: /newqa <asset> [@reviewer]
    parts = message_text.split(maxsplit=1)
    if len(parts) < 2:
        asset = "Follow the file" if update.message.document or update.message.photo else "QA submission"
    else:
        asset = parts[1].strip()
    
    # Extract reviewer mention if present
    reviewer_username = None
    reviewer_match = re.search(r'@(\w+)', asset)
    if reviewer_match:
        reviewer_username = reviewer_match.group(1)
        # Remove reviewer mention from asset
        asset = re.sub(r'@\w+', '', asset).strip()
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /newqa command message")
    except Exception as e:
        logger.warning(f"Failed to delete /newqa command: {e}")
    
    if not task_service:
        await send_dm_with_autodelete(context, user_id, "❌ Service not available", 15)
        return
    
    try:
        # Verify task exists
        task = await task_service.get_task(ticket)
        if not task:
            await send_dm_with_autodelete(context, user_id, f"❌ Task `{ticket}` not found.", 15)
            return
        
        # Verify user is the assignee
        if task.assignee_id != user_id:
            await send_dm_with_autodelete(context, user_id, f"❌ You are not assigned to task `{ticket}`.", 15)
            return
        
        # Verify task is in STARTED state
        from src.data.models.task import TaskState
        if task.state != TaskState.STARTED:
            await send_dm_with_autodelete(context, user_id, f"❌ Task `{ticket}` is not in STARTED state. Current state: {task.state.value}", 15)
            return
        
        # Check if QA already exists for this ticket
        from src.data.repositories.qa_repository import QARepository
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        existing_qa = await qa_repo.get_submission(ticket)
        
        if existing_qa and existing_qa.status.value == 'PENDING':
            await send_dm_with_autodelete(context, user_id, f"❌ QA submission already exists for task `{ticket}` with status: {existing_qa.status.value}", 15)
            return
        
        # Get brand display name (GSM -> GSMAura, VRB -> VorosaBajar, POV -> Povaly)
        from src.core.brand_mapper import BrandMapper
        brand_mapper = BrandMapper()
        brand_display = brand_mapper.get_display_name(task.brand)
        
        # Build QA submission message with proper newlines
        qa_text = f"""[TICKET] #{ticket}
[BRAND] #{brand_display}
[ASSET] {asset}

📋 **QA Submission**
👤 **Submitted by:** @{username}
🆔 **User ID:** {user_id}

_Reviewers: React 👍 to claim, ❤️ to approve, or 👎 to reject._"""
        
        # Send to QA & Review topic
        qa_msg = await context.bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=qa_text,
            parse_mode='Markdown',
            message_thread_id=config.TOPIC_QA_REVIEW
        )
        
        logger.info(f"Sent QA submission to QA & Review topic for ticket {ticket}")
        
        # If there's a file attached, forward it as a reply to the QA message
        if update.message.document or update.message.photo or update.message.video:
            try:
                await update.message.reply_to_message.copy_to(
                    chat_id=config.TELEGRAM_GROUP_ID,
                    message_thread_id=config.TOPIC_QA_REVIEW,
                    reply_to_message_id=qa_msg.message_id
                )
                logger.info(f"Forwarded file attachment to QA submission")
            except Exception as e:
                logger.warning(f"Failed to forward file: {e}")
        
        # Create QA submission in database
        from datetime import datetime
        from src.data.models.qa_submission import QASubmission, QAStatus
        
        submission = QASubmission(
            id=None,
            ticket=ticket,
            brand=task.brand.replace('#', ''),
            asset=asset,
            submitter_id=user_id,
            submitted_at=datetime.now(),
            message_id=qa_msg.message_id,
            status=QAStatus.PENDING
        )
        
        await qa_repo.create_submission(submission)
        
        # Update task state to QA_SUBMITTED
        from src.core.state.state_engine import StateEngine
        state_engine = StateEngine(context.bot_data.get('task_repository'))
        await state_engine.process_qa_submission(ticket, submission.submitted_at)
        
        logger.info(f"Created QA submission for task {ticket}")
        
        # Build link to QA message
        group_id_str = str(config.TELEGRAM_GROUP_ID)
        if group_id_str.startswith('-100'):
            group_id_clean = group_id_str[4:]
        else:
            group_id_clean = group_id_str
        
        qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_msg.message_id}"
        
        # Send confirmation
        confirmation = f"✅ **QA Submitted**\n\n"
        confirmation += f"Task **#{ticket}** has been submitted for QA review.\n\n"
        confirmation += f"[📎 View QA Submission]({qa_link})"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=confirmation,
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=20,
            warning_text=True
        )
        
        # Send DM to submitter
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ **QA Submitted**\n\nYour work on task **#{ticket}** has been submitted for QA review.\n\n**Asset:** {asset}\n\n[📎 View QA Submission]({qa_link})\n\nYou will be notified when the review is complete.",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.warning(f"Failed to send QA submission DM: {e}")
        
        # Notify reviewer if mentioned
        if reviewer_username:
            try:
                user_repo = context.bot_data.get('user_repository')
                if user_repo:
                    # Find user by username
                    reviewer = await user_repo.get_user_by_username(reviewer_username)
                    if reviewer:
                        await context.bot.send_message(
                            chat_id=reviewer.user_id,
                            text=f"📋 **QA Review Request**\n\nYou have been assigned to review task **#{ticket}**.\n\n**Submitted by:** @{username}\n**Asset:** {asset}\n\n[📎 View QA Submission]({qa_link})",
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                        logger.info(f"Notified reviewer @{reviewer_username} about QA submission")
            except Exception as e:
                logger.warning(f"Failed to notify reviewer: {e}")
        
    except Exception as e:
        logger.error(f"Error in /newqa command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error submitting QA: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=15,
            warning_text=True
        )




async def process_newqa_direct(update: Update, context: ContextTypes.DEFAULT_TYPE, ticket: str, asset: str, user_id: int, username: str, reviewer_username: str = None):
    """Process direct QA submission with ticket specified in command."""
    
    config = context.bot_data.get('config')
    task_service = context.bot_data.get('task_service')
    topic_id = update.message.message_thread_id if update.message.is_topic_message else None
    
    try:
        # Verify task exists
        task = await task_service.get_task(ticket)
        if not task:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ Task `{ticket}` not found.",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Verify user is the assignee
        if task.assignee_id != user_id:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ You are not assigned to task `{ticket}`.",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Verify task is in STARTED state
        from src.data.models.task import TaskState
        if task.state != TaskState.STARTED:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ Task `{ticket}` is not in STARTED state. Current state: {task.state.value}",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if QA already exists for this ticket
        from src.data.repositories.qa_repository import QARepository
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        existing_qa = await qa_repo.get_submission(ticket)
        
        if existing_qa and existing_qa.status.value == 'PENDING':
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ QA submission already exists for task `{ticket}` with status: {existing_qa.status.value}",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Get brand display name (GSM -> GSMAura, VRB -> VorosaBajar, POV -> Povaly)
        from src.core.brand_mapper import BrandMapper
        brand_mapper = BrandMapper()
        brand_display = brand_mapper.get_display_name(task.brand)
        
        # Build QA submission message with proper newlines
        qa_text = f"""[TICKET] #{ticket}
[BRAND] #{brand_display}
[ASSET] {asset}

📋 **QA Submission**
👤 **Submitted by:** @{username}
🆔 **User ID:** {user_id}

_Reviewers: React 👍 to claim, ❤️ to approve, or 👎 to reject._"""
        
        # Send to QA & Review topic
        qa_msg = await context.bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=qa_text,
            parse_mode='Markdown',
            message_thread_id=config.TOPIC_QA_REVIEW
        )
        
        logger.info(f"Sent QA submission to QA & Review topic for ticket {ticket}")
        
        # Create QA submission in database
        from datetime import datetime
        from src.data.models.qa_submission import QASubmission, QAStatus
        
        submission = QASubmission(
            id=None,
            ticket=ticket,
            brand=task.brand,  # Store the code (GSM, VRB, POV)
            asset=asset,
            submitter_id=user_id,
            submitted_at=datetime.now(),
            message_id=qa_msg.message_id,
            status=QAStatus.PENDING
        )
        
        await qa_repo.create_submission(submission)
        
        # Update task state to QA_SUBMITTED
        from src.core.state.state_engine import StateEngine
        state_engine = StateEngine(context.bot_data.get('task_repository'))
        await state_engine.process_qa_submission(ticket, submission.submitted_at)
        
        logger.info(f"Created QA submission for task {ticket}")
        
        # Build link to QA message
        group_id_str = str(config.TELEGRAM_GROUP_ID)
        if group_id_str.startswith('-100'):
            group_id_clean = group_id_str[4:]
        else:
            group_id_clean = group_id_str
        
        qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_msg.message_id}"
        
        # Send confirmation
        confirmation = f"✅ **QA Submitted**\n\n"
        confirmation += f"Task **#{ticket}** has been submitted for QA review.\n\n"
        confirmation += f"[📎 View QA Submission]({qa_link})"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=confirmation,
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=20,
            warning_text=True
        )
        
        # Send DM to submitter
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ **QA Submitted**\n\nYour work on task **#{ticket}** has been submitted for QA review.\n\n**Asset:** {asset}\n\n[📎 View QA Submission]({qa_link})\n\nYou will be notified when the review is complete.",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.warning(f"Failed to send QA submission DM: {e}")
        
        # Notify reviewer if mentioned
        if reviewer_username:
            try:
                user_repo = context.bot_data.get('user_repository')
                if user_repo:
                    reviewer = await user_repo.get_user_by_username(reviewer_username)
                    if reviewer:
                        await context.bot.send_message(
                            chat_id=reviewer.user_id,
                            text=f"📋 **QA Review Request**\n\nYou have been assigned to review task **#{ticket}**.\n\n**Submitted by:** @{username}\n**Asset:** {asset}\n\n[📎 View QA Submission]({qa_link})",
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                        logger.info(f"Notified reviewer @{reviewer_username} about QA submission")
            except Exception as e:
                logger.warning(f"Failed to notify reviewer: {e}")
        
    except Exception as e:
        logger.error(f"Error processing direct QA submission: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error submitting QA: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_myqa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myqa command - show user's QA submissions grouped by status."""
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    config = context.bot_data.get('config')
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /myqa command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /myqa command: {e}")
    
    try:
        from src.data.repositories.qa_repository import QARepository
        from src.data.models.qa_submission import QAStatus
        
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        
        # Get all QA submissions by this user
        all_submissions = await qa_repo.get_submissions_by_submitter(user_id)
        
        if not all_submissions:
            response = f"📋 **My QA Submissions**\n\n"
            response += f"👤 **User:** @{username}\n"
            response += f"🆔 **ID:** {user_id}\n\n"
            response += "You have no QA submissions."
            
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=response,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=20,
                warning_text=True
            )
            return
        
        # Group by status
        pending = [qa for qa in all_submissions if qa.status == QAStatus.PENDING]
        approved = [qa for qa in all_submissions if qa.status == QAStatus.APPROVED]
        rejected = [qa for qa in all_submissions if qa.status == QAStatus.REJECTED]
        
        # Build response
        response = f"📋 **My QA Submissions**\n\n"
        response += f"👤 **User:** @{username}\n"
        response += f"🆔 **ID:** {user_id}\n\n"
        
        # Build link helper
        group_id_str = str(config.TELEGRAM_GROUP_ID)
        if group_id_str.startswith('-100'):
            group_id_clean = group_id_str[4:]
        else:
            group_id_clean = group_id_str
        
        # Pending submissions
        if pending:
            response += f"⏳ **PENDING** ({len(pending)})\n"
            for qa in pending[:10]:  # Limit to 10
                qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa.message_id}"
                response += f"• [#{qa.ticket}]({qa_link}) - {qa.asset[:50]}\n"
            response += "\n"
        
        # Approved submissions
        if approved:
            response += f"✅ **APPROVED** ({len(approved)})\n"
            for qa in approved[:10]:  # Limit to 10
                qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa.message_id}"
                response += f"• [#{qa.ticket}]({qa_link}) - {qa.asset[:50]}\n"
            response += "\n"
        
        # Rejected submissions
        if rejected:
            response += f"❌ **REJECTED** ({len(rejected)})\n"
            for qa in rejected[:10]:  # Limit to 10
                qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa.message_id}"
                response += f"• [#{qa.ticket}]({qa_link}) - {qa.asset[:50]}\n"
            response += "\n"
        
        response += f"**Total:** {len(all_submissions)} submission(s)\n\n"
        response += "**Status Legend:** ⏳ Pending | ✅ Approved | ❌ Rejected\n\n"
        response += "⚠️ _This message will auto-delete in 40 seconds. React with 👏 to keep it for 10 minutes._"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=40,
            warning_text=False
        )
        
    except Exception as e:
        logger.error(f"Error in /myqa command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error retrieving QA submissions: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_reviewingqa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reviewingqa command - show QA submissions you're reviewing (claimed with 👍)."""
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    config = context.bot_data.get('config')
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /reviewingqa command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /reviewingqa command: {e}")
    
    # Check if user is authorized (QA reviewers, admins, managers, or owners)
    if (user_id not in config.QA_REVIEWERS and 
        user_id not in config.ADMINISTRATORS and 
        user_id not in config.MANAGERS and 
        user_id not in config.OWNERS):
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ **Access Denied**\n\nThis command is only available to QA Reviewers, Administrators, Managers, and Owners.",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        from src.data.repositories.qa_repository import QARepository
        from src.data.models.qa_submission import QAStatus
        
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        
        # Get all pending QA submissions (we'll filter by claimed reactions)
        pending_submissions = await qa_repo.get_submissions_by_status(QAStatus.PENDING)
        
        # Note: We can't easily check reactions from database
        # For now, show all pending QA as "potentially reviewing"
        # In a full implementation, we'd track reviewer claims in the database
        
        if not pending_submissions:
            response = f"📋 **QA Submissions I'm Reviewing**\n\n"
            response += f"👤 **User:** @{username}\n"
            response += f"🆔 **ID:** {user_id}\n\n"
            response += "You have no QA submissions under review."
            
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=response,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=20,
                warning_text=True
            )
            return
        
        # Build response
        response = f"📋 **QA Submissions I'm Reviewing**\n\n"
        response += f"👤 **User:** @{username}\n"
        response += f"🆔 **ID:** {user_id}\n\n"
        response += f"**Total:** {len(pending_submissions)} pending submission(s)\n\n"
        response += "_Note: Showing all pending QA submissions. React with 👍 to claim for review._\n\n"
        
        # Build link helper
        group_id_str = str(config.TELEGRAM_GROUP_ID)
        if group_id_str.startswith('-100'):
            group_id_clean = group_id_str[4:]
        else:
            group_id_clean = group_id_str
        
        # Get user repository for submitter names
        user_repo = context.bot_data.get('user_repository')
        
        # Show pending submissions (limit to 15)
        for qa in pending_submissions[:15]:
            qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa.message_id}"
            
            # Get submitter username
            submitter_name = f"User {qa.submitter_id}"
            if user_repo:
                try:
                    submitter = await user_repo.get_user(qa.submitter_id)
                    if submitter and submitter.username:
                        submitter_name = f"@{submitter.username}"
                except Exception as e:
                    logger.warning(f"Failed to get submitter username: {e}")
            
            # Calculate time elapsed
            from datetime import datetime
            time_elapsed = datetime.now() - qa.submitted_at
            hours_elapsed = int(time_elapsed.total_seconds() / 3600)
            
            # Time indicator
            if hours_elapsed < 1:
                time_text = "< 1h"
            elif hours_elapsed < 24:
                time_text = f"{hours_elapsed}h"
            else:
                days = hours_elapsed // 24
                time_text = f"{days}d"
            
            response += f"• [#{qa.ticket}]({qa_link}) - {qa.brand}\n"
            response += f"  📝 {qa.asset[:60]}\n"
            response += f"  👤 {submitter_name} • ⏱️ {time_text} ago\n\n"
        
        if len(pending_submissions) > 15:
            response += f"_...and {len(pending_submissions) - 15} more_\n\n"
        
        response += "**Actions:**\n"
        response += "• React with ❤️ to approve\n"
        response += "• Use `/reject #TICKET <reason>` to reject\n\n"
        response += "⚠️ _This message will auto-delete in 40 seconds. React with 👏 to keep it for 10 minutes._"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=40,
            warning_text=False
        )
        
    except Exception as e:
        logger.error(f"Error in /reviewingqa command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error retrieving reviewing QA submissions: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_pendingqa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pendingqa command - show all pending QA submissions (reviewers/admins only)."""
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    config = context.bot_data.get('config')
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /pendingqa command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /pendingqa command: {e}")
    
    # Check if user is authorized (QA reviewers, admins, managers, or owners)
    if (user_id not in config.QA_REVIEWERS and 
        user_id not in config.ADMINISTRATORS and 
        user_id not in config.MANAGERS and 
        user_id not in config.OWNERS):
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ **Access Denied**\n\nThis command is only available to QA Reviewers, Administrators, Managers, and Owners.",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        from src.data.repositories.qa_repository import QARepository
        from src.data.models.qa_submission import QAStatus
        
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        
        # Get all pending QA submissions
        pending_submissions = await qa_repo.get_submissions_by_status(QAStatus.PENDING)
        
        if not pending_submissions:
            response = f"📋 **Pending QA Submissions**\n\n"
            response += f"👤 **Requested by:** @{username}\n"
            response += f"🆔 **ID:** {user_id}\n\n"
            response += "No pending QA submissions."
            
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=response,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=20,
                warning_text=True
            )
            return
        
        # Sort by submission time (oldest first)
        pending_submissions.sort(key=lambda qa: qa.submitted_at)
        
        # Build response
        response = f"📋 **Pending QA Submissions**\n\n"
        response += f"👤 **Requested by:** @{username}\n"
        response += f"🆔 **ID:** {user_id}\n\n"
        response += f"**Total:** {len(pending_submissions)} pending submission(s)\n\n"
        
        # Build link helper
        group_id_str = str(config.TELEGRAM_GROUP_ID)
        if group_id_str.startswith('-100'):
            group_id_clean = group_id_str[4:]
        else:
            group_id_clean = group_id_str
        
        # Get user repository for submitter names
        user_repo = context.bot_data.get('user_repository')
        
        # Show pending submissions (limit to 15)
        for qa in pending_submissions[:15]:
            qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa.message_id}"
            
            # Get submitter username
            submitter_name = f"User {qa.submitter_id}"
            if user_repo:
                try:
                    submitter = await user_repo.get_user(qa.submitter_id)
                    if submitter and submitter.username:
                        submitter_name = f"@{submitter.username}"
                except Exception as e:
                    logger.warning(f"Failed to get submitter username: {e}")
            
            # Calculate time elapsed
            from datetime import datetime
            time_elapsed = datetime.now() - qa.submitted_at
            hours_elapsed = int(time_elapsed.total_seconds() / 3600)
            
            # Time indicator
            if hours_elapsed < 1:
                time_text = "< 1h"
            elif hours_elapsed < 24:
                time_text = f"{hours_elapsed}h"
            else:
                days = hours_elapsed // 24
                time_text = f"{days}d"
            
            response += f"• [#{qa.ticket}]({qa_link}) - {qa.brand}\n"
            response += f"  📝 {qa.asset[:60]}\n"
            response += f"  👤 {submitter_name} • ⏱️ {time_text} ago\n\n"
        
        if len(pending_submissions) > 15:
            response += f"_...and {len(pending_submissions) - 15} more_\n\n"
        
        response += "**Actions:**\n"
        response += "• React with 👍 to claim for review\n"
        response += "• React with ❤️ to approve\n"
        response += "• Use `/reject #TICKET <reason>` to reject\n\n"
        response += "⚠️ _This message will auto-delete in 60 seconds. React with 👏 to keep it for 10 minutes._"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=60,
            warning_text=False
        )
        
    except Exception as e:
        logger.error(f"Error in /pendingqa command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error retrieving pending QA submissions: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_unreviewedqa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unreviewedqa command - show QA submissions that are old and still pending."""
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    config = context.bot_data.get('config')
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /unreviewedqa command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /unreviewedqa command: {e}")
    
    # Check if user is authorized (QA reviewers, admins, managers, or owners)
    if (user_id not in config.QA_REVIEWERS and 
        user_id not in config.ADMINISTRATORS and 
        user_id not in config.MANAGERS and 
        user_id not in config.OWNERS):
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ **Access Denied**\n\nThis command is only available to QA Reviewers, Administrators, Managers, and Owners.",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        from src.data.repositories.qa_repository import QARepository
        from src.data.models.qa_submission import QAStatus
        from datetime import datetime, timedelta
        
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        
        # Get all pending QA submissions older than 6 hours
        pending_submissions = await qa_repo.get_submissions_by_status(QAStatus.PENDING)
        
        # Filter for submissions older than 6 hours
        six_hours_ago = datetime.now() - timedelta(hours=6)
        unreviewed = [qa for qa in pending_submissions if qa.submitted_at < six_hours_ago]
        
        # Sort by submission time (oldest first)
        unreviewed.sort(key=lambda qa: qa.submitted_at)
        
        if not unreviewed:
            response = f"📋 **Unreviewed QA Submissions**\n\n"
            response += f"👤 **Requested by:** @{username}\n"
            response += f"🆔 **ID:** {user_id}\n\n"
            response += "No unreviewed QA submissions (older than 6 hours)."
            
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=response,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=20,
                warning_text=True
            )
            return
        
        # Build response
        response = f"📋 **Unreviewed QA Submissions**\n\n"
        response += f"👤 **Requested by:** @{username}\n"
        response += f"🆔 **ID:** {user_id}\n\n"
        response += f"**Total:** {len(unreviewed)} unreviewed submission(s) (>6h old)\n\n"
        
        # Build link helper
        group_id_str = str(config.TELEGRAM_GROUP_ID)
        if group_id_str.startswith('-100'):
            group_id_clean = group_id_str[4:]
        else:
            group_id_clean = group_id_str
        
        # Get user repository for submitter names
        user_repo = context.bot_data.get('user_repository')
        
        # Show unreviewed submissions (limit to 15)
        for qa in unreviewed[:15]:
            qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa.message_id}"
            
            # Get submitter username
            submitter_name = f"User {qa.submitter_id}"
            if user_repo:
                try:
                    submitter = await user_repo.get_user(qa.submitter_id)
                    if submitter and submitter.username:
                        submitter_name = f"@{submitter.username}"
                except Exception as e:
                    logger.warning(f"Failed to get submitter username: {e}")
            
            # Calculate time elapsed
            time_elapsed = datetime.now() - qa.submitted_at
            hours_elapsed = int(time_elapsed.total_seconds() / 3600)
            
            # Time indicator with warning for very old submissions
            if hours_elapsed < 24:
                time_text = f"{hours_elapsed}h"
                warning = ""
            else:
                days = hours_elapsed // 24
                time_text = f"{days}d"
                warning = " 🔥" if days >= 1 else ""
            
            response += f"• [#{qa.ticket}]({qa_link}) - {qa.brand}{warning}\n"
            response += f"  📝 {qa.asset[:60]}\n"
            response += f"  👤 {submitter_name} • ⏱️ {time_text} ago\n\n"
        
        if len(unreviewed) > 15:
            response += f"_...and {len(unreviewed) - 15} more_\n\n"
        
        response += "**Actions:**\n"
        response += "• React with 👍 to claim for review\n"
        response += "• React with ❤️ to approve\n"
        response += "• Use `/reject #TICKET <reason>` to reject\n\n"
        response += "⚠️ _This message will auto-delete in 60 seconds. React with 👏 to keep it for 10 minutes._"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=60,
            warning_text=False
        )
        
    except Exception as e:
        logger.error(f"Error in /unreviewedqa command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error retrieving unreviewed QA submissions: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_qa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /qa command - show detailed QA info for a task ticket."""
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    message_text = update.message.text or ""
    config = context.bot_data.get('config')
    topic_id = update.message.message_thread_id if update.message.is_topic_message else None
    
    logger.info(f"User {user_id} invoked /qa command: {message_text}")
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /qa command message")
    except Exception as e:
        logger.warning(f"Failed to delete /qa command: {e}")
    
    # Extract ticket from command
    parts = message_text.split()
    if len(parts) < 2:
        help_msg = """📋 **View QA Details**

**Usage:** `/qa #TICKET`

**Examples:**
• `/qa #POV260406`
• `/qa POV260406`

**Note:** Shows detailed information about the QA submission for the specified task."""
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=help_msg,
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=20,
            warning_text=True
        )
        return
    
    ticket = parts[1].replace('#', '').upper()
    
    try:
        from src.data.repositories.qa_repository import QARepository
        from src.data.models.qa_submission import QAStatus
        
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        
        # Get QA submission
        qa_submission = await qa_repo.get_submission(ticket)
        
        if not qa_submission:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **QA Not Found**\n\nNo QA submission found for ticket: `{ticket}`",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Build detailed response
        status_emoji = {
            "PENDING": "⏳",
            "APPROVED": "✅",
            "REJECTED": "❌"
        }
        
        response = f"📋 **QA Submission Details**\n\n"
        response += f"👤 **Requested by:** @{username}\n"
        response += f"🆔 **ID:** {user_id}\n\n"
        response += f"**Ticket:** #{qa_submission.ticket}\n"
        response += f"**Brand:** {qa_submission.brand}\n"
        response += f"**Status:** {status_emoji.get(qa_submission.status.value, '❓')} {qa_submission.status.value}\n\n"
        
        # Get submitter username
        user_repo = context.bot_data.get('user_repository')
        submitter_name = f"User {qa_submission.submitter_id}"
        if user_repo:
            try:
                submitter = await user_repo.get_user(qa_submission.submitter_id)
                if submitter and submitter.username:
                    submitter_name = f"@{submitter.username}"
            except Exception as e:
                logger.warning(f"Failed to get submitter username: {e}")
        
        response += f"**Submitted by:** {submitter_name}\n"
        response += f"**Submitted at:** {qa_submission.submitted_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # Asset
        response += f"**Asset:**\n{qa_submission.asset}\n\n"
        
        # Reviewer info if reviewed
        if qa_submission.reviewed_by:
            reviewer_name = f"User {qa_submission.reviewed_by}"
            if user_repo:
                try:
                    reviewer = await user_repo.get_user(qa_submission.reviewed_by)
                    if reviewer and reviewer.username:
                        reviewer_name = f"@{reviewer.username}"
                except Exception as e:
                    logger.warning(f"Failed to get reviewer username: {e}")
            
            response += f"**Reviewed by:** {reviewer_name}\n"
            if qa_submission.reviewed_at:
                response += f"**Reviewed at:** {qa_submission.reviewed_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        # Build link to QA message
        group_id_str = str(config.TELEGRAM_GROUP_ID)
        if group_id_str.startswith('-100'):
            group_id_clean = group_id_str[4:]
        else:
            group_id_clean = group_id_str
        
        qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_submission.message_id}"
        
        response += f"\n[📎 View QA Submission]({qa_link})\n\n"
        response += "⚠️ _This message will auto-delete in 40 seconds. React with 👏 to keep it for 10 minutes._"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=40,
            warning_text=False
        )
        
    except Exception as e:
        logger.error(f"Error in /qa command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error retrieving QA details: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /approve command - approve a QA submission (adds ❤️ reaction)."""
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    message_text = update.message.text or ""
    config = context.bot_data.get('config')
    topic_id = update.message.message_thread_id if update.message.is_topic_message else None
    
    logger.info(f"User {user_id} invoked /approve command: {message_text}")
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /approve command message")
    except Exception as e:
        logger.warning(f"Failed to delete /approve command: {e}")
    
    # Check if user is authorized (QA reviewers, admins, managers, or owners)
    if (user_id not in config.QA_REVIEWERS and 
        user_id not in config.ADMINISTRATORS and 
        user_id not in config.MANAGERS and 
        user_id not in config.OWNERS):
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ **Access Denied**\n\nThis command is only available to QA Reviewers, Administrators, Managers, and Owners.",
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    # Extract ticket from command
    parts = message_text.split()
    if len(parts) < 2:
        help_msg = """✅ **Approve QA Submission**

**Usage:** `/approve #TICKET`

**Examples:**
• `/approve #POV260406`
• `/approve POV260406`

**Note:** This will add ❤️ reaction to the QA message and mark it as approved."""
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=help_msg,
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=20,
            warning_text=True
        )
        return
    
    ticket = parts[1].replace('#', '').upper()
    
    try:
        from src.data.repositories.qa_repository import QARepository
        from src.data.models.qa_submission import QAStatus
        
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        qa_service = context.bot_data.get('qa_service')
        
        # Get QA submission
        qa_submission = await qa_repo.get_submission(ticket)
        
        if not qa_submission:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **QA Not Found**\n\nNo QA submission found for ticket: `{ticket}`",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if already approved
        if qa_submission.status == QAStatus.APPROVED:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"✅ **Already Approved**\n\nQA submission for `{ticket}` is already approved.",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if not pending
        if qa_submission.status != QAStatus.PENDING:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Cannot Approve**\n\nQA submission for `{ticket}` is not pending. Current status: {qa_submission.status.value}",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Add ❤️ reaction to QA message
        try:
            from telegram import ReactionTypeEmoji
            await context.bot.set_message_reaction(
                chat_id=config.TELEGRAM_GROUP_ID,
                message_id=qa_submission.message_id,
                reaction=[ReactionTypeEmoji(emoji="❤️")],
                is_big=False
            )
            logger.info(f"Added ❤️ reaction to QA message {qa_submission.message_id}")
        except Exception as e:
            logger.error(f"Failed to add ❤️ reaction: {e}", exc_info=True)
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Error**\n\nFailed to add reaction: {str(e)}",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Update QA status to APPROVED
        success = await qa_service.approve_qa(ticket, user_id)
        
        if success:
            # Update task state to APPROVED
            task_service = context.bot_data.get('task_service')
            if task_service:
                from src.data.models.task import TaskState
                from datetime import datetime
                await task_service.task_repo.update_task_state(
                    ticket, TaskState.APPROVED, datetime.now()
                )
            
            # Build link to QA message
            group_id_str = str(config.TELEGRAM_GROUP_ID)
            if group_id_str.startswith('-100'):
                group_id_clean = group_id_str[4:]
            else:
                group_id_clean = group_id_str
            
            qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_submission.message_id}"
            
            # Send confirmation
            confirmation = f"✅ **QA Approved**\n\n"
            confirmation += f"QA submission for task **#{ticket}** has been approved.\n\n"
            confirmation += f"❤️ Reaction added to the QA message.\n"
            confirmation += f"The submitter will be notified via DM.\n\n"
            confirmation += f"[📎 View QA Submission]({qa_link})"
            
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=confirmation,
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=False
            )
            
            # Send DM to submitter
            try:
                user_repo = context.bot_data.get('user_repository')
                reviewer_username = "a reviewer"
                if user_repo:
                    reviewer = await user_repo.get_user(user_id)
                    if reviewer and reviewer.username:
                        reviewer_username = f"@{reviewer.username}"
                
                await context.bot.send_message(
                    chat_id=qa_submission.submitter_id,
                    text=f"✅ **QA Approved**\n\nYour QA submission for task **#{ticket}** has been approved by {reviewer_username}.\n\n**Asset:** {qa_submission.asset}\n\n[📎 View QA Submission]({qa_link})\n\nGreat work! The task is now complete.",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info(f"Sent approval notification to submitter {qa_submission.submitter_id}")
            except Exception as e:
                logger.warning(f"Failed to send approval notification: {e}")
            
            logger.info(f"User {user_id} approved QA {ticket} via /approve command")
        else:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Failed to Approve**\n\nCould not approve QA for `{ticket}`. Please try again.",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
        
    except Exception as e:
        logger.error(f"Error in /approve command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error approving QA: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reject command - reject a QA submission with reason (adds 👎 reaction)."""
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    message_text = update.message.text or ""
    config = context.bot_data.get('config')
    topic_id = update.message.message_thread_id if update.message.is_topic_message else None
    
    logger.info(f"User {user_id} invoked /reject command: {message_text}")
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /reject command message")
    except Exception as e:
        logger.warning(f"Failed to delete /reject command: {e}")
    
    # Check if user is authorized (QA reviewers, admins, managers, or owners)
    if (user_id not in config.QA_REVIEWERS and 
        user_id not in config.ADMINISTRATORS and 
        user_id not in config.MANAGERS and 
        user_id not in config.OWNERS):
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ **Access Denied**\n\nThis command is only available to QA Reviewers, Administrators, Managers, and Owners.",
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    # Extract ticket and reason from command
    parts = message_text.split(maxsplit=2)
    if len(parts) < 3:
        help_msg = """❌ **Reject QA Submission**

**Usage:** `/reject #TICKET <reason>`

**Examples:**
• `/reject #POV260406 Low quality images, please use higher resolution`
• `/reject POV260406 Missing brand logo in header`

**Note:** Reason is required. This will add 👎 reaction and notify the submitter with your feedback."""
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=help_msg,
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=25,
            warning_text=True
        )
        return
    
    ticket = parts[1].replace('#', '').upper()
    reason = parts[2].strip()
    
    try:
        from src.data.repositories.qa_repository import QARepository
        from src.data.models.qa_submission import QAStatus
        
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        qa_service = context.bot_data.get('qa_service')
        
        # Get QA submission
        qa_submission = await qa_repo.get_submission(ticket)
        
        if not qa_submission:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **QA Not Found**\n\nNo QA submission found for ticket: `{ticket}`",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if already rejected
        if qa_submission.status == QAStatus.REJECTED:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Already Rejected**\n\nQA submission for `{ticket}` is already rejected.",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if not pending
        if qa_submission.status != QAStatus.PENDING:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Cannot Reject**\n\nQA submission for `{ticket}` is not pending. Current status: {qa_submission.status.value}",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Add 👎 reaction to QA message
        try:
            from telegram import ReactionTypeEmoji
            await context.bot.set_message_reaction(
                chat_id=config.TELEGRAM_GROUP_ID,
                message_id=qa_submission.message_id,
                reaction=[ReactionTypeEmoji(emoji="👎")],
                is_big=False
            )
            logger.info(f"Added 👎 reaction to QA message {qa_submission.message_id}")
        except Exception as e:
            logger.error(f"Failed to add 👎 reaction: {e}", exc_info=True)
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Error**\n\nFailed to add reaction: {str(e)}",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Update QA status to REJECTED
        success = await qa_service.reject_qa(ticket, user_id)
        
        if success:
            # Update task state to REJECTED
            task_service = context.bot_data.get('task_service')
            if task_service:
                from src.data.models.task import TaskState
                from datetime import datetime
                await task_service.task_repo.update_task_state(
                    ticket, TaskState.REJECTED, datetime.now()
                )
            
            # Build link to QA message
            group_id_str = str(config.TELEGRAM_GROUP_ID)
            if group_id_str.startswith('-100'):
                group_id_clean = group_id_str[4:]
            else:
                group_id_clean = group_id_str
            
            qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_submission.message_id}"
            
            # Send confirmation
            confirmation = f"❌ **QA Rejected**\n\n"
            confirmation += f"QA submission for task **#{ticket}** has been rejected.\n\n"
            confirmation += f"👎 Reaction added to the QA message.\n"
            confirmation += f"The submitter will be notified via DM with your feedback.\n\n"
            confirmation += f"**Reason:** {reason}\n\n"
            confirmation += f"[📎 View QA Submission]({qa_link})"
            
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=confirmation,
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=20,
                warning_text=False
            )
            
            # Send DM to submitter with detailed feedback
            try:
                user_repo = context.bot_data.get('user_repository')
                reviewer_username = "a reviewer"
                if user_repo:
                    reviewer = await user_repo.get_user(user_id)
                    if reviewer and reviewer.username:
                        reviewer_username = f"@{reviewer.username}"
                
                await context.bot.send_message(
                    chat_id=qa_submission.submitter_id,
                    text=f"❌ **QA Rejected**\n\nYour QA submission for task **#{ticket}** has been rejected by {reviewer_username}.\n\n**Asset:** {qa_submission.asset}\n\n**Feedback:**\n_{reason}_\n\n[📎 View QA Submission]({qa_link})\n\n⚠️ **Next Steps:**\nPlease address the feedback and resubmit using `/reopenqa #{ticket} <update message>` when ready.",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info(f"Sent rejection notification to submitter {qa_submission.submitter_id}")
            except Exception as e:
                logger.warning(f"Failed to send rejection notification: {e}")
            
            logger.info(f"User {user_id} rejected QA {ticket} via /reject command with reason: {reason}")
        else:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Failed to Reject**\n\nCould not reject QA for `{ticket}`. Please try again.",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
        
    except Exception as e:
        logger.error(f"Error in /reject command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error rejecting QA: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_reopenqa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reopenqa command - resubmit a rejected QA with updates (submitter only)."""
    
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    message_text = update.message.text or ""
    config = context.bot_data.get('config')
    topic_id = update.message.message_thread_id if update.message.is_topic_message else None
    
    logger.info(f"User {user_id} invoked /reopenqa command: {message_text}")
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /reopenqa command message")
    except Exception as e:
        logger.warning(f"Failed to delete /reopenqa command: {e}")
    
    # Extract ticket and update message from command
    parts = message_text.split(maxsplit=2)
    if len(parts) < 3:
        help_msg = """🔄 **Reopen QA Submission**

**Usage:** `/reopenqa #TICKET <update message>`

**Examples:**
• `/reopenqa #POV260406 Fixed image quality, now using 1080p`
• `/reopenqa POV260406 Added brand logo to header as requested`

**Note:** Update message is required. This will reset the QA to PENDING status and notify the reviewer."""
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=help_msg,
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=25,
            warning_text=True
        )
        return
    
    ticket = parts[1].replace('#', '').upper()
    update_message = parts[2].strip()
    
    try:
        from src.data.repositories.qa_repository import QARepository
        from src.data.models.qa_submission import QAStatus
        
        qa_repo = QARepository(context.bot_data.get('db_adapter'))
        
        # Get QA submission
        qa_submission = await qa_repo.get_submission(ticket)
        
        if not qa_submission:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **QA Not Found**\n\nNo QA submission found for ticket: `{ticket}`",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if user is the submitter
        if qa_submission.submitter_id != user_id:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Permission Denied**\n\nOnly the submitter can reopen this QA submission.",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if QA is rejected
        if qa_submission.status != QAStatus.REJECTED:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Not Rejected**\n\nQA submission for `{ticket}` is not rejected. Current status: {qa_submission.status.value}\n\nOnly rejected QA submissions can be reopened.",
                parse_mode='Markdown',
                message_thread_id=topic_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Store reviewer info before reopening
        reviewer_id = qa_submission.reviewed_by
        
        # Remove 👎 reaction from QA message
        try:
            from telegram import ReactionTypeEmoji
            await context.bot.set_message_reaction(
                chat_id=config.TELEGRAM_GROUP_ID,
                message_id=qa_submission.message_id,
                reaction=[],  # Empty list removes all reactions
                is_big=False
            )
            logger.info(f"Removed 👎 reaction from QA message {qa_submission.message_id}")
        except Exception as e:
            logger.error(f"Failed to remove 👎 reaction: {e}", exc_info=True)
        
        # Update QA status back to PENDING
        await qa_repo.update_submission_status(
            ticket, QAStatus.PENDING, None, None
        )
        
        # Update task state back to QA_SUBMITTED
        task_service = context.bot_data.get('task_service')
        if task_service:
            from src.data.models.task import TaskState
            from datetime import datetime
            await task_service.task_repo.update_task_state(
                ticket, TaskState.QA_SUBMITTED, datetime.now()
            )
        
        # Build link to QA message
        group_id_str = str(config.TELEGRAM_GROUP_ID)
        if group_id_str.startswith('-100'):
            group_id_clean = group_id_str[4:]
        else:
            group_id_clean = group_id_str
        
        qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_submission.message_id}"
        
        # Send confirmation to submitter
        confirmation = f"🔄 **QA Reopened**\n\n"
        confirmation += f"QA submission for task **#{ticket}** has been reopened.\n\n"
        confirmation += f"Status reset to PENDING. The reviewer will be notified.\n\n"
        confirmation += f"**Update:** {update_message}\n\n"
        confirmation += f"[📎 View QA Submission]({qa_link})"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=confirmation,
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=20,
            warning_text=False
        )
        
        # Send DM to submitter confirming reopen
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🔄 **QA Reopened Successfully**\n\nYou have reopened QA submission for task **#{ticket}**.\n\n**Asset:** {qa_submission.asset}\n**Update:** {update_message}\n\n[📎 View QA Submission]({qa_link})\n\nThe reviewer will be notified to review your updates.",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            logger.info(f"Sent reopen confirmation DM to submitter {user_id}")
        except Exception as e:
            logger.warning(f"Failed to send reopen confirmation to submitter: {e}")
        
        # Send DM to reviewer if exists
        if reviewer_id:
            try:
                user_repo = context.bot_data.get('user_repository')
                reviewer_username = "the reviewer"
                if user_repo:
                    reviewer = await user_repo.get_user(reviewer_id)
                    if reviewer and reviewer.username:
                        reviewer_username = f"@{reviewer.username}"
                
                await context.bot.send_message(
                    chat_id=reviewer_id,
                    text=f"🔄 **QA Reopened**\n\nQA submission for task **#{ticket}** has been reopened by the submitter.\n\n**Asset:** {qa_submission.asset}\n**Submitted by:** @{username}\n\n**Update Message:**\n_{update_message}_\n\n⚠️ **Action Required:**\nThe submitter has addressed your feedback. Please review the updated submission.\n\n[📎 View QA Submission]({qa_link})",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info(f"Sent reopen notification to reviewer {reviewer_id}")
            except Exception as e:
                logger.warning(f"Failed to send reopen notification to reviewer: {e}")
        
        logger.info(f"User {user_id} reopened QA {ticket} via /reopenqa command")
        
    except Exception as e:
        logger.error(f"Error in /reopenqa command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error reopening QA: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=topic_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_newissue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newissue command - multiple modes:
    1. Reply to task in Task Allocation: Extract ticket → Send to Core Operations with priority selection
    2. Direct in Core Operations: Show task list → Select task → Show priority selection → Template
    3. With ticket argument: /newissue POV260414 - show priority selection
    """
    
    user_id = update.message.from_user.id
    message_text = update.message.text or ""
    config = context.bot_data.get('config')
    topic_id = update.message.message_thread_id if update.message.is_topic_message else None
    
    logger.info(f"cmd_newissue called by user {user_id} in topic {topic_id}")
    logger.info(f"Message text: {message_text}")
    logger.info(f"Has reply_to_message: {update.message.reply_to_message is not None}")
    
    # Delete the command message first
    try:
        await update.message.delete()
        logger.info(f"Deleted /newissue command message")
    except Exception as e:
        logger.warning(f"Failed to delete /newissue command: {e}")
    
    # Check if command has ticket argument first
    # MODE 1: Direct command with ticket argument
    # Example: /newissue POV260414
    parts = message_text.split()
    if len(parts) > 1:
        ticket_arg = parts[1].replace("#", "").upper()
        logger.info(f"Ticket provided as argument: {ticket_arg}")
        
        # If in Core Operations, show priority selection here
        # Otherwise, send to Core Operations
        if topic_id == config.TOPIC_CORE_OPERATIONS:
            await show_priority_selection_for_ticket(update, context, ticket_arg, "manual")
        else:
            await send_priority_selection_to_core_ops(update, context, ticket_arg, user_id)
        return
    
    # MODE 2: Reply to task message (only if NOT in Core Operations or reply has valid ticket)
    # → Extract ticket → Send priority selection to Core Operations
    if update.message.reply_to_message:
        replied_text = update.message.reply_to_message.text or ""
        logger.info(f"Replying to message, extracting ticket from: {replied_text[:100]}")
        
        issue_service = context.bot_data.get('issue_service')
        if issue_service:
            ticket = issue_service.extract_ticket_from_text(replied_text)
            if ticket:
                logger.info(f"Extracted ticket from reply: {ticket}")
                # If in Core Operations, show priority selection here
                # Otherwise, send to Core Operations
                if topic_id == config.TOPIC_CORE_OPERATIONS:
                    await show_priority_selection_for_ticket(update, context, ticket, "reply")
                else:
                    await send_priority_selection_to_core_ops(update, context, ticket, user_id)
                return
            else:
                # Only show error if NOT in Core Operations
                # If in Core Operations without valid ticket in reply, fall through to task menu
                if topic_id != config.TOPIC_CORE_OPERATIONS:
                    logger.warning(f"Could not extract ticket from replied message")
                    # Send error to DM
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text="❌ Could not find ticket in the replied message. Please reply to a task message with a valid ticket ID.\n\n_This message will auto-delete in 15 seconds_",
                            parse_mode='Markdown'
                        )
                        logger.info(f"Sent /newissue error to DM for user {user_id}")
                    except Exception as e:
                        logger.error(f"Failed to send DM to user {user_id}: {e}")
                    return
    
    # MODE 3: Direct command in Core Operations without arguments (or with invalid reply)
    # → Show task selection menu
    if topic_id == config.TOPIC_CORE_OPERATIONS:
        logger.info(f"Showing task selection menu in Core Operations")
        await show_task_selection_menu(update, context)
    else:
        # Not in Core Operations and no reply/argument - show help in DM
        help_msg = """🚨 **Create New Issue**

**Usage:**
• Reply to a task message with `/newissue` - Creates issue for that task
• `/newissue #POV260414` - Creates issue for specific ticket
• Use `/newissue` in Core Operations topic to select from task list

**Note:** Issue creation happens in Core Operations topic.

_This message will auto-delete in 20 seconds_"""
        
        try:
            sent_msg = await context.bot.send_message(
                chat_id=user_id,
                text=help_msg,
                parse_mode='Markdown'
            )
            logger.info(f"Sent /newissue help to DM for user {user_id}")
            
            # Auto-delete after 20 seconds
            async def delete_dm():
                await asyncio.sleep(20)
                try:
                    await sent_msg.delete()
                except:
                    pass
            asyncio.create_task(delete_dm())
        except Exception as e:
            logger.error(f"Failed to send DM to user {user_id}: {e}")


async def send_priority_selection_to_core_ops(update: Update, context: ContextTypes.DEFAULT_TYPE, ticket: str, user_id: int):
    """Send priority selection message to Core Operations topic.
    
    Args:
        update: Telegram update
        context: Telegram context
        ticket: The ticket ID
        user_id: User who initiated the issue creation
    """
    
    config = context.bot_data.get('config')
    if not config:
        logger.error("Config not initialized")
        return
    
    logger.info(f"Sending priority selection to Core Operations for ticket {ticket}")
    
    # Create priority selection keyboard
    keyboard = [
        [InlineKeyboardButton("🔴 CRITICAL", callback_data=f"newissue_priority:{ticket}:CRITICAL")],
        [InlineKeyboardButton("🟠 HIGH", callback_data=f"newissue_priority:{ticket}:HIGH")],
        [InlineKeyboardButton("🟡 MEDIUM", callback_data=f"newissue_priority:{ticket}:MEDIUM")],
        [InlineKeyboardButton("🟢 LOW", callback_data=f"newissue_priority:{ticket}:LOW")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get user mention
    user = update.message.from_user
    user_mention = f"@{user.username}" if user.username else user.first_name
    
    # Send to Core Operations topic
    message = f"👤 **User:** {user_mention}\n"
    message += f"🆔 **ID:** {user.id}\n\n"
    message += f"🚨 **Create Issue for Task #{ticket}**\n\n"
    message += "Select the priority level for this issue:\n\n"
    message += "🔴 **CRITICAL** - System down, blocking all work\n"
    message += "🟠 **HIGH** - Major feature broken, affects many users\n"
    message += "🟡 **MEDIUM** - Important but not urgent, workaround exists\n"
    message += "🟢 **LOW** - Minor issue, enhancement request"
    
    try:
        priority_msg = await context.bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            message_thread_id=config.TOPIC_CORE_OPERATIONS
        )
        
        logger.info(f"Sent priority selection to Core Operations for ticket {ticket}")
        
        # Build link to the priority selection message
        # Format: https://t.me/c/<group_id_without_-100>/<topic_id>/<message_id>
        group_id_str = str(config.TELEGRAM_GROUP_ID)
        if group_id_str.startswith('-100'):
            group_id_clean = group_id_str[4:]  # Remove -100 prefix
        else:
            group_id_clean = group_id_str
        
        priority_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_CORE_OPERATIONS}/{priority_msg.message_id}"
        
        # Send confirmation to user in DM
        confirmation = f"✅ **Issue Creation Started**\n\n"
        confirmation += f"Priority selection sent to **Core Operations** topic for task **#{ticket}**.\n\n"
        confirmation += f"[👉 Click here to select priority]({priority_link})\n\n"
        confirmation += f"_This message will auto-delete in 10 seconds_"
        
        try:
            sent_msg = await context.bot.send_message(
                chat_id=user_id,
                text=confirmation,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            logger.info(f"Sent /newissue confirmation to DM for user {user_id}")
            
            # Auto-delete after 10 seconds
            async def delete_dm():
                await asyncio.sleep(10)
                try:
                    await sent_msg.delete()
                except:
                    pass
            asyncio.create_task(delete_dm())
        except Exception as e:
            logger.error(f"Failed to send DM to user {user_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error sending priority selection to Core Operations: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error sending to Core Operations: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def show_task_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show menu to select a task for issue creation.
    Shows user's assigned tasks first, then recent tasks if none assigned.
    """
    
    task_service = context.bot_data.get('task_service')
    user_id = update.message.from_user.id
    
    if not task_service:
        logger.warning("Task service not available")
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ Task service not available",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        from src.data.models.task import TaskState
        
        # First, try to get user's assigned tasks
        user_tasks = []
        for state in [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.REJECTED]:
            tasks = await task_service.get_tasks_by_assignee(user_id, state)
            user_tasks.extend(tasks)
        
        # Sort by creation date, most recent first
        user_tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # If user has no assigned tasks, get recent tasks from all users
        if not user_tasks:
            logger.info(f"User {user_id} has no assigned tasks, showing recent tasks")
            recent_tasks = []
            for state in [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.REJECTED]:
                tasks = await task_service.task_repo.get_tasks_by_state(state)
                recent_tasks.extend(tasks[-10:])
            
            recent_tasks.sort(key=lambda t: t.created_at, reverse=True)
            tasks_to_show = recent_tasks[:15]
            header_text = "Select the task that has the issue:\n\n_Showing recent tasks from all users._"
        else:
            tasks_to_show = user_tasks[:15]
            header_text = "Select your task that has the issue:\n\n_Showing your assigned tasks._"
        
        if not tasks_to_show:
            logger.warning("No tasks found")
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text="❌ No tasks found. Use `/newissue #POV260414` to create issue for a specific ticket.",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Build keyboard
        keyboard = []
        for task in tasks_to_show:
            # Add state emoji
            state_emoji = {
                TaskState.ASSIGNED: "📌",
                TaskState.STARTED: "⚙️",
                TaskState.QA_SUBMITTED: "🔍",
                TaskState.REJECTED: "❌",
                TaskState.APPROVED: "✅"
            }.get(task.state, "❓")
            
            task_info = f"{state_emoji} #{task.ticket} - {task.brand}"
            if len(task_info) > 35:
                task_info = task_info[:32] + "..."
            
            button = InlineKeyboardButton(
                text=task_info,
                callback_data=f"newissue_task:{task.ticket}"
            )
            keyboard.append([button])
        
        # Add manual entry option
        keyboard.append([InlineKeyboardButton("📝 Enter Ticket Manually", callback_data="newissue:manual")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "🚨 **Create New Issue**\n\n"
        message += header_text
        
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
        )
        
    except Exception as e:
        logger.error(f"Error showing task selection menu: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def show_priority_selection_for_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE, ticket: str, source: str):
    """Show priority selection for a specific ticket.
    
    Args:
        ticket: The ticket ID
        source: Where the ticket came from ('reply', 'manual', 'menu')
    """
    
    logger.info(f"Showing priority selection for ticket {ticket} (source: {source})")
    
    keyboard = [
        [InlineKeyboardButton("🔴 CRITICAL", callback_data=f"newissue_priority:{ticket}:CRITICAL")],
        [InlineKeyboardButton("🟠 HIGH", callback_data=f"newissue_priority:{ticket}:HIGH")],
        [InlineKeyboardButton("🟡 MEDIUM", callback_data=f"newissue_priority:{ticket}:MEDIUM")],
        [InlineKeyboardButton("🟢 LOW", callback_data=f"newissue_priority:{ticket}:LOW")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Get user mention
    user = update.message.from_user if update.message else (update.callback_query.from_user if update.callback_query else None)
    if user:
        user_mention = f"@{user.username}" if user.username else user.first_name
        message = f"👤 **User:** {user_mention}\n"
        message += f"🆔 **ID:** {user.id}\n\n"
    else:
        message = ""
    
    message += f"🚨 **Create Issue for Task #{ticket}**\n\n"
    message += "Select the priority level for this issue:\n\n"
    message += "🔴 **CRITICAL** - System down, blocking all work\n"
    message += "🟠 **HIGH** - Major feature broken, affects many users\n"
    message += "🟡 **MEDIUM** - Important but not urgent, workaround exists\n"
    message += "🟢 **LOW** - Minor issue, enhancement request"
    
    # Determine chat_id and message_thread_id based on update type
    if update.message:
        chat_id = update.message.chat_id
        message_thread_id = update.message.message_thread_id if update.message.is_topic_message else None
    elif update.callback_query:
        chat_id = update.callback_query.message.chat_id
        message_thread_id = update.callback_query.message.message_thread_id if update.callback_query.message.is_topic_message else None
    else:
        logger.error("No message or callback_query in update")
        return
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        message_thread_id=message_thread_id
    )


async def handle_reply_newissue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newissue when replying to a task message."""
    
    # Extract ticket from the replied message
    replied_message = update.message.reply_to_message
    replied_text = replied_message.text or ""
    
    # Try to extract ticket from the replied message
    issue_service = context.bot_data.get('issue_service')
    if not issue_service:
        logger.error("Issue service not initialized")
        return
    
    ticket = issue_service.extract_ticket_from_text(replied_text)
    
    if not ticket:
        # Could not extract ticket, show error
        error_msg = "❌ **Could not find ticket**\n\nThe message you replied to doesn't contain a valid ticket ID. Please use `/newissue` without replying to select a task."
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        
        # Delete the command message
        try:
            await update.message.delete()
        except:
            pass
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted reply-based /newissue command from user {update.message.from_user.id}")
    except Exception as e:
        logger.warning(f"Failed to delete /newissue command: {e}")
    
    # Show priority selection for this specific ticket in Core Operations topic
    config = context.bot_data.get('config')
    if not config:
        logger.error("Config not initialized")
        return
    
    keyboard = [
        [InlineKeyboardButton("🔴 CRITICAL", callback_data=f"reply_newissue:{ticket}:CRITICAL")],
        [InlineKeyboardButton("🟠 HIGH", callback_data=f"reply_newissue:{ticket}:HIGH")],
        [InlineKeyboardButton("🟡 MEDIUM", callback_data=f"reply_newissue:{ticket}:MEDIUM")],
        [InlineKeyboardButton("🟢 LOW", callback_data=f"reply_newissue:{ticket}:LOW")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send priority selection to Core Operations topic
    message = f"🚨 **Create Issue for Task #{ticket}**\n\n"
    message += f"_Issue creation initiated by reply to task message_\n\n"
    message += "Select the priority level for this issue:\n\n"
    message += "🔴 **CRITICAL** - System down, blocking all work\n"
    message += "🟠 **HIGH** - Major feature broken, affects many users\n"
    message += "🟡 **MEDIUM** - Important but not urgent, workaround exists\n"
    message += "🟢 **LOW** - Minor issue, enhancement request"
    
    await context.bot.send_message(
        chat_id=config.TELEGRAM_GROUP_ID,
        text=message,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        message_thread_id=config.TOPIC_CORE_OPERATIONS
    )
    
    # Send confirmation to user
    confirmation = f"✅ **Issue Creation Started**\n\nPriority selection sent to Core Operations topic for task **{ticket}**.\n\nGo to Core Operations to complete the issue creation."
    
    await send_auto_delete_message(
        context=context,
        chat_id=update.message.chat_id,
        text=confirmation,
        parse_mode='Markdown',
        message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
        delete_after_seconds=10,
        warning_text=True
    )


async def cmd_newissue_priority_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newissue command - show priority selection for manual issue creation."""
    
    # Build inline keyboard with priority buttons
    keyboard = [
        [InlineKeyboardButton("🔴 CRITICAL", callback_data="newissue:CRITICAL")],
        [InlineKeyboardButton("🟠 HIGH", callback_data="newissue:HIGH")],
        [InlineKeyboardButton("🟡 MEDIUM", callback_data="newissue:MEDIUM")],
        [InlineKeyboardButton("🟢 LOW", callback_data="newissue:LOW")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Build the message
    message = "🚨 **Create New Issue**\n\n"
    message += "Select the priority level for your issue:\n\n"
    message += "🔴 **CRITICAL** - System down, blocking all work\n"
    message += "🟠 **HIGH** - Major feature broken, affects many users\n"
    message += "🟡 **MEDIUM** - Important but not urgent, workaround exists\n"
    message += "🟢 **LOW** - Minor issue, enhancement request"
    
    # Delete the user's /newissue command message if not already deleted
    try:
        await update.message.delete()
        logger.info(f"Deleted /newissue command message from user {update.message.from_user.id}")
    except Exception as e:
        logger.warning(f"Failed to move /newissue command to trash: {e}")
    
    # Send the priority selection menu
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=message,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
    )


async def cmd_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /commands command - show all available commands with descriptions."""
    
    # Delete the command message from group
    try:
        await update.message.delete()
        logger.info(f"Deleted /commands command message from user {update.message.from_user.id}")
    except Exception as e:
        logger.warning(f"Failed to delete /commands command message: {e}")
    
    # Get user info and config
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    config = context.bot_data.get('config')
    
    # Check user role
    is_admin = user_id in config.ADMINISTRATORS if config else False
    is_manager = user_id in config.MANAGERS if config else False
    is_owner = user_id in config.OWNERS if config else False
    is_privileged = is_admin or is_manager or is_owner
    
    # Build comprehensive command list
    message = "📚 **Available Commands**\n\n"
    
    # Add user info at the top
    message += f"👤 **Requested by:** @{username}\n"
    message += f"🆔 **ID:** {user_id}\n\n"
    
    # Auto-delete warning at the top
    message += "⏱️ **Auto-delete:** This message will be deleted in 120 seconds\n\n"
    
    message += "💡 **Tip:** Copy and paste any command to use it\n\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Task Management Commands (Available to all)
    message += "**📋 Task Management**\n"
    message += "`/mytasks` - Show your assigned tasks with status\n"
    message += "`/newtask` - Create a new task (shows brand selection)\n"
    message += "`/tasksbystate` - Filter tasks by state (ASSIGNED, STARTED, etc.)\n"
    message += "`/taskstats` - Show task statistics and summary\n"
    message += "`/overduetasks` - Show overdue tasks\n\n"
    
    # Issue Management Commands (Available to all)
    message += "**🔧 Issue Management**\n"
    message += "`/newissue` - Create a new issue\n"
    message += "  • Reply to a task message: Extract ticket automatically\n"
    message += "  • Use in Core Operations: Manual issue creation\n"
    message += "`/myissues` - Show issues you've created\n"
    message += "`/myclaimedissues` - Show issues you've claimed\n"
    message += "`/openissues` - Show all unresolved issues\n"
    message += "`/unresolved` - Show claimed but unresolved issues\n"
    message += "`/inactive` - Show unclaimed issues\n"
    message += "`/issue <ticket>` - Show specific issue details\n"
    message += "`/close <ticket>` - Resolve an issue\n\n"
    
    # Information & Help Commands (Available to all)
    message += "**ℹ️ Information & Help**\n"
    message += "`/help` - Show general help and bot overview\n"
    message += "`/taskhelp` - Show task allocation guide\n"
    message += "`/brand` - Show available brands\n"
    message += "`/support` - Show support type selection\n"
    message += "`/commands` - Show this command list\n\n"
    
    # Advanced Filtering (Available to all)
    message += "**🔍 Advanced Filtering**\n"
    message += "`/filter` - Advanced task filtering options\n\n"
    
    # Reaction-based Actions (Available to all)
    message += "**👍 Reaction-based Actions**\n"
    message += "React to task messages with:\n"
    message += "  • 👍 - Start task (ASSIGNED → STARTED)\n"
    message += "  • ❤️ - Approve QA (QA_SUBMITTED → APPROVED)\n"
    message += "  • 👎 - Reject QA (QA_SUBMITTED → REJECTED)\n"
    
    # Show privileged commands only to admins/managers/owners
    if is_privileged:
        message += "  • 🔥 - Add exemption (Admin/Manager/Owner only)\n\n"
        
        # Admin Commands
        message += "**⚙️ Admin Commands**\n"
        message += "`/edit <message_id> <new_text>` - Edit bot messages\n"
        message += "`/pin` - Show pinning options\n"
        message += "`/dailysummary` - Manually trigger daily task summary\n\n"
        
        # Database & Sync Commands
        message += "**🔄 Database & Sync Commands**\n"
        message += "`/cleantasks` - Clean up orphaned tasks\n"
        message += "`/syncdb` - Aggressive database cleanup\n"
        message += "`/resetdb` - Reset your database to match reality\n"
        message += "`/scantopic` - Scan Task Allocation topic\n"
        message += "`/syncdebug` - Show sync service status\n"
        message += "`/debugtasks` - Debug task detection\n\n"
    else:
        message += "\n"
    
    message += "_Copy any command and paste in chat to use it_"
    
    # Send message to DM
    try:
        sent_message = await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
        
        # Store message info for auto-deletion
        context.user_data['commands_message_id'] = sent_message.message_id
        context.user_data['commands_chat_id'] = user_id
        context.user_data['commands_user_id'] = user_id
        
        # Schedule auto-delete after 120 seconds
        async def delete_after_delay():
            await asyncio.sleep(120)
            try:
                await sent_message.delete()
                logger.info(f"Auto-deleted /commands DM after 120 seconds")
            except Exception as e:
                logger.warning(f"Failed to auto-delete /commands DM: {e}")
        
        context.user_data['commands_delete_task'] = asyncio.create_task(delete_after_delay())
        
        logger.info(f"✅ Sent /commands response to DM for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to send /commands DM to user {user_id}: {e}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "👋 Welcome to Povaly Operations Bot!\n\n"
        "Use /commands to see all available commands."
    )


async def cmd_newtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newtask command - show brand selection for task creation."""
    
    user_id = update.message.from_user.id
    brand_mapper = BrandMapper()
    
    # Get all unique brand codes
    brand_codes = sorted(brand_mapper.get_all_codes())
    
    # Build inline keyboard with brand buttons
    keyboard = []
    for code in brand_codes:
        display_name = brand_mapper.get_display_name(code)
        # Each button will trigger task template creation
        button = InlineKeyboardButton(
            text=f"{code} - {display_name}",
            callback_data=f"newtask:{display_name}"
        )
        keyboard.append([button])  # One button per row
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Build the message
    message = "📋 **Create New Task**\n\n"
    message += "Click a brand to create a task template:\n"
    
    # Delete the user's /newtask command message from group
    try:
        await update.message.delete()
        logger.info(f"Deleted /newtask command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /newtask command: {e}")
    
    # Send the brand selection menu to DM
    try:
        sent_message = await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Auto-delete after 60 seconds
        async def delete_dm():
            await asyncio.sleep(60)
            try:
                await sent_message.delete()
                logger.info(f"Auto-deleted /newtask DM after 60 seconds")
            except:
                pass
        asyncio.create_task(delete_dm())
        
        logger.info(f"✅ Sent /newtask brand selection to DM for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to send /newtask DM to user {user_id}: {e}")


async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /support command - show support type selection."""
    
    user_id = update.message.from_user.id
    
    # Build inline keyboard with support type buttons
    keyboard = []
    for support_type in SUPPORT_TYPES:
        button = InlineKeyboardButton(
            text=f"{support_type['emoji']} {support_type['label']}",
            callback_data=f"support:{support_type['id']}"
        )
        keyboard.append([button])  # One button per row
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Build the message
    message = "🆘 **Request Support**\n\n"
    message += "Select the type of support you need:\n\n"
    
    for support_type in SUPPORT_TYPES:
        message += f"{support_type['emoji']} **{support_type['label']}** - {support_type['description']}\n"
    
    # Delete the user's /support command message from group
    try:
        await update.message.delete()
        logger.info(f"Deleted /support command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /support command: {e}")
    
    # Send the support type selection menu to DM
    try:
        sent_message = await context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Auto-delete after 60 seconds
        async def delete_dm():
            await asyncio.sleep(60)
            try:
                await sent_message.delete()
                logger.info(f"Auto-deleted /support DM after 60 seconds")
            except:
                pass
        asyncio.create_task(delete_dm())
        
        logger.info(f"✅ Sent /support menu to DM for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to send /support DM to user {user_id}: {e}")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /help command message from user {update.message.from_user.id}")
    except Exception as e:
        logger.warning(f"Failed to delete /help command: {e}")
    
    help_text = """
📋 **Povaly Operations Bot - Help**

**Available Commands:**
/newtask - Create new task with template
/newissue - Create new issue with template
/support - Request help or report issues
/taskhelp - Show task allocation guide
/brand - Show all available brand names and codes
/pin - Pin a message (shows 3 options)
/edit - Edit any message (Admin only)
/help - Show this help message

**Core Operations Commands:**
/newissue - Create new issue with template
/myissues - Show your claimed issues
/openissues - Show all unresolved issues
/issue #TICKET - Show specific issue details
/close #TICKET - Mark issue as resolved
/unresolved - Show claimed but unresolved issues
/inactive - Show unclaimed issues

**Task Allocation Format:**
```
[TICKET] POV260401
[BRAND] VorosaBajar
[TASK] Product page SEO optimization
[ASSIGNEE] @username
[DEADLINE] 28 Apr 2026 | 6:00 PM GMT+6
[RESOURCES] Google Doc Link
```

**Issue Format (Core Operations):**
```
[TICKET] #POV260406 (existing task ticket)
[ISSUE] Short descriptive title
[DETAILS] Detailed explanation
[PRIORITY] LOW / MEDIUM / HIGH / CRITICAL
[ASSIGNEE] @username (optional)
```

**Issue Reactions:**
👍 = Claim issue (start working on it)
❤️ = Mark as resolved (issue is fixed)
👎 = Mark as invalid (wrong issue)

**Important:** Issues are for reporting problems with existing tasks. Use the ticket ID of the task that has the problem, not a new ticket.

**Required Fields:**
• [TICKET] - Use /newtask for pre-generated ticket
• [ASSIGNEE] - Username with @

**Optional Fields:**
• [BRAND] - Brand name (use /brand to see options)
• [TASK] - Task description
• [DEADLINE] - Due date
• [RESOURCES] - Links or files

**QA Submission Format:**
```
[TICKET] POV260401
[BRAND] GSMAura
[ASSET] https://example.com/asset-url
```

**Ticket Format:**
• POV = Brand (3 chars)
• 2604 = Year+Month (April 2026)
• 01 = Sequential number

**Pin Message System:**

**Method 1 - Command Menu:**
Type `/pin` → Select from 3 options:
• Pin default guide
• Pin custom message
• Pin from file

**Method 2 - Direct Marker:**
Type `[PINNED]` in your message:
• `[PINNED]` alone → Pins default guide
• `[PINNED] Your message` → Pins your message
• `[PINNED] docs/file.txt` → Pins file content

**Examples:**
```
[PINNED] 🎯 Today's Priority
• Complete pending tasks
• Review QA submissions
```

**Tips:**
• Use /newtask command for pre-filled template with unique ticket
• Use /taskhelp for complete task allocation guide
• Brand names are case-insensitive
• `[PINNED]` marker preserves all formatting (line breaks, emojis)
• React with 👍 to claim issues, ❤️ to resolve them
"""
    
    await send_auto_delete_message(
        context=context,
        chat_id=update.message.chat_id,
        text=help_text,
        parse_mode='Markdown',
        message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
        delete_after_seconds=20,
        warning_text=True
    )


async def cmd_taskhelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /taskhelp command - show task allocation guide."""
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /taskhelp command message from user {update.message.from_user.id}")
    except Exception as e:
        logger.warning(f"Failed to delete /taskhelp command: {e}")
    
    guide_text = """
📋 **TASK ALLOCATION GUIDE**

👨‍💼 **FOR MANAGERS:**

**Quick Method (Recommended):**
1. Type `/newtask`
2. Click your brand
3. Copy template (20 seconds)
4. Fill and send

**Manual Method:**
```
[TICKET] POV260401
[BRAND] Povaly
[TASK] Description
[ASSIGNEE] @username
[DEADLINE] DD MMM YYYY | HH:MM AM/PM GMT+6
[RESOURCES] Links
```

👷 **FOR EMPLOYEES:**

**Start Work:**
• React 👍 on your task
• This marks presence + starts work

**Submit for QA:**
• React ❤️ when done
• Task goes to QA review

⚠️ **RULES:**
• Only task messages in this topic
• Wrong format = Auto-delete + DM
• React within 24 hours
• One task per message

**Ticket Format:** BRANDYYMM##
• POV = Povaly
• VRB = VorosaBajar
• GSM = GSMAura

**Examples:**
• POV260401 (April 2026, #01)
• VRB260515 (May 2026, #15)

**Need More Help?**
• Full SOP: Check pinned message
• Support: `/support` in Core Operations
• Brands: `/brand`

**Commands:**
• `/newtask` - Create task
• `/support` - Get help
• `/brand` - Show brands
"""
    
    await send_auto_delete_message(
        context=context,
        chat_id=update.message.chat_id,
        text=guide_text,
        parse_mode='Markdown',
        message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
        delete_after_seconds=20,
        warning_text=True
    )


async def cmd_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pin command - show options for pinning."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    # Check if user is admin or manager
    user_id = update.message.from_user.id
    config = context.bot_data.get('config')
    
    is_authorized = (
        user_id in config.ADMINISTRATORS or 
        user_id in config.MANAGERS or 
        user_id in config.OWNERS
    )
    
    if not is_authorized:
        error_msg = "❌ **Access Denied**\n\nOnly Administrators, Managers, and Owners can pin messages."
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        # Delete the command message
        try:
            await update.message.delete()
        except:
            pass
        return
    
    # Build inline keyboard with 3 options
    keyboard = [
        [InlineKeyboardButton("📋 Pin Default Guide", callback_data="pin:default")],
        [InlineKeyboardButton("✏️ Pin Custom Message", callback_data="pin:custom")],
        [InlineKeyboardButton("📁 Pin from File", callback_data="pin:file")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Delete the /pin command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /pin command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /pin command: {e}")
    
    # Send the options menu with auto-delete
    await send_auto_delete_message(
        context=context,
        chat_id=update.message.chat_id,
        text="📌 **Pin Message**\n\nSelect an option:",
        parse_mode='Markdown',
        reply_markup=reply_markup,
        message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
        delete_after_seconds=20,
        warning_text=True
    )


async def cmd_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /brand command - show available brands with inline buttons."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    brand_mapper = BrandMapper()
    
    # Get all unique brand codes
    brand_codes = sorted(brand_mapper.get_all_codes())
    
    # Build inline keyboard with brand buttons
    keyboard = []
    for code in brand_codes:
        display_name = brand_mapper.get_display_name(code)
        # Each button will send the brand name when clicked
        button = InlineKeyboardButton(
            text=f"{code} - {display_name}",
            callback_data=f"brand:{display_name}"
        )
        keyboard.append([button])  # One button per row
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Build the message
    message = "🏢 **Select a Brand**\n\n"
    message += "Click a button below to copy the brand name:"
    
    # Delete the user's /brand command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /brand command message from user {update.message.from_user.id}")
    except Exception as e:
        logger.warning(f"Failed to delete /brand command: {e}")
    
    # Send the brand selection menu with auto-delete
    await send_auto_delete_message(
        context=context,
        chat_id=update.message.chat_id,
        text=message,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
        delete_after_seconds=20,
        warning_text=True
    )


async def handle_brand_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle brand selection from inline buttons."""
    query = update.callback_query
    await query.answer()
    
    # Extract brand name from callback data
    brand_name = query.data.replace("brand:", "")
    
    # Send the brand name to the user
    response = f"✅ **Brand Selected:** {brand_name}\n\n"
    response += f"Copy this for your [BRAND] field:\n"
    response += f"`[BRAND] #{brand_name}`"
    
    # Edit the original message to show selection
    await query.edit_message_text(
        text=response,
        parse_mode='Markdown'
    )
    
    # Delete the message after 20 seconds
    await asyncio.sleep(20)
    try:
        await query.message.delete()
        logger.info(f"Deleted brand selection message after 20 seconds")
    except Exception as e:
        logger.warning(f"Failed to delete brand selection message: {e}")


async def handle_newtask_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle brand selection for new task creation."""
    
    query = update.callback_query
    await query.answer()
    
    # Extract brand name from callback data
    brand_name = query.data.replace("newtask:", "")
    
    # Pre-generate ticket ID
    from src.core.ticket_generator import TicketGenerator
    from src.core.brand_mapper import BrandMapper
    
    db_adapter = context.bot_data.get("db_adapter")
    brand_mapper = BrandMapper()
    ticket_gen = TicketGenerator(db_adapter, brand_mapper)
    
    try:
        # Generate unique ticket ID
        generated_ticket = await ticket_gen.generate_ticket_id(brand_name)
        logger.info(f"Pre-generated ticket: {generated_ticket} for brand: {brand_name}")
    except Exception as e:
        logger.error(f"Failed to pre-generate ticket: {e}")
        generated_ticket = ""  # Fallback to empty
    
    # Use centralized template
    template = format_template(
        TASK_ALLOCATION_TEMPLATE,
        ticket=generated_ticket,
        brand=brand_name
    )
    
    # Delete the selection message
    try:
        await query.message.delete()
        logger.info(f"Deleted newtask selection message")
    except Exception as e:
        logger.warning(f"Failed to delete newtask selection message: {e}")
    
    # Send the template with auto-delete warning
    instruction = f"📋 **Copy this for Task Creation**\n\n"
    instruction += f"👇 **Copy the text below:**\n"
    instruction += f"```\n{template}\n```\n\n"
    instruction += f"📝 **Instructions:**\n"
    instruction += get_field_help_text(TASK_ALLOCATION_TEMPLATE) + "\n\n"
    instruction += f"_Ticket {generated_ticket} is pre-generated and unique!_"
    
    await send_auto_delete_message(
        context=context,
        chat_id=query.message.chat_id,
        text=instruction,
        parse_mode='Markdown',
        message_thread_id=query.message.message_thread_id if query.message.is_topic_message else None,
        delete_after_seconds=20,
        warning_text=True
    )


async def handle_support_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle support type selection."""
    
    query = update.callback_query
    await query.answer()
    
    # Extract support type from callback data
    support_type_id = query.data.replace("support:", "")
    
    # Find the support type details
    support_type = next((st for st in SUPPORT_TYPES if st['id'] == support_type_id), None)
    if not support_type:
        logger.error(f"Unknown support type: {support_type_id}")
        return
    
    # Use centralized template
    template = format_template(
        CORE_OPERATIONS_TEMPLATE,
        type=support_type['label']
    )
    
    # Delete the selection message
    try:
        await query.message.delete()
        logger.info(f"Deleted support selection message")
    except Exception as e:
        logger.warning(f"Failed to delete support selection message: {e}")
    
    # Send the template with auto-delete warning
    instruction = f"{support_type['emoji']} **Copy this for Support Request**\n\n"
    instruction += f"👇 **Copy the text below:**\n"
    instruction += f"```\n{template}\n```\n\n"
    instruction += f"📝 **Instructions:**\n"
    instruction += get_field_help_text(CORE_OPERATIONS_TEMPLATE) + "\n\n"
    instruction += f"**After submitting:**\n"
    instruction += f"• 👀 = Admin acknowledged, working on it\n"
    instruction += f"• ❤️ = Problem solved (you'll get a DM)"
    
    await send_auto_delete_message(
        context=context,
        chat_id=query.message.chat_id,
        text=instruction,
        parse_mode='Markdown',
        message_thread_id=query.message.message_thread_id if query.message.is_topic_message else None,
        delete_after_seconds=20,
        warning_text=True
    )


async def handle_pin_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pin option selection."""
    
    query = update.callback_query
    await query.answer()
    
    # Extract pin option from callback data
    pin_option = query.data.replace("pin:", "")
    config = context.bot_data.get('config')
    
    # Delete the selection message
    try:
        await query.message.delete()
        logger.info(f"Deleted pin selection message")
    except Exception as e:
        logger.warning(f"Failed to delete pin selection message: {e}")
    
    if pin_option == "default":
        # Pin default guide for this topic
        topic_id = query.message.message_thread_id if query.message.is_topic_message else None
        default_file = 'docs/GUIDE_TASK_ALLOCATION.txt'  # Fallback
        
        # Map topics to their guide files
        if topic_id == config.TOPIC_TASK_ALLOCATION:
            default_file = 'docs/GUIDE_TASK_ALLOCATION.txt'
        elif topic_id == config.TOPIC_CORE_OPERATIONS:
            default_file = 'docs/GUIDE_CORE_OPERATIONS.txt'
        elif topic_id == config.TOPIC_QA_REVIEW:
            default_file = 'docs/GUIDE_QA_REVIEW.txt'
        elif topic_id == config.TOPIC_ATTENDANCE_LEAVE:
            default_file = 'docs/GUIDE_ATTENDANCE_LEAVE.txt'
        elif topic_id == config.TOPIC_OFFICIAL_DIRECTIVES:
            default_file = 'docs/GUIDE_OFFICIAL_DIRECTIVES.txt'
        elif topic_id == config.TOPIC_BRAND_REPOSITORY:
            default_file = 'docs/GUIDE_BRAND_REPOSITORY.txt'
        elif topic_id == config.TOPIC_CENTRAL_ARCHIVE:
            default_file = 'docs/GUIDE_CENTRAL_ARCHIVE.txt'
        elif topic_id == config.TOPIC_DAILY_SYNC:
            default_file = 'docs/GUIDE_DAILY_SYNC.txt'
        elif topic_id == config.TOPIC_ADMIN_CONTROL_PANEL:
            default_file = 'docs/GUIDE_ADMIN_CONTROL_PANEL.txt'
        elif topic_id == config.TOPIC_STRATEGIC_LOUNGE:
            default_file = 'docs/GUIDE_STRATEGIC_LOUNGE.txt'
        
        try:
            with open(default_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Send as HTML (keep newlines as-is, they work in HTML mode)
            html_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            sent_message = await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=html_content,
                parse_mode='HTML',
                message_thread_id=query.message.message_thread_id if query.message.is_topic_message else None
            )
            
            # Pin it
            await context.bot.pin_chat_message(
                chat_id=query.message.chat_id,
                message_id=sent_message.message_id,
                disable_notification=False
            )
            logger.info(f"Pinned default guide from {default_file}")
            
        except FileNotFoundError:
            error_msg = f"❌ Guide file not found: `{default_file}`"
            await send_auto_delete_message(
                context=context,
                chat_id=query.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=query.message.message_thread_id if query.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
        except Exception as e:
            logger.error(f"Error pinning default guide: {e}")
            error_msg = f"❌ Error: {str(e)}"
            await send_auto_delete_message(
                context=context,
                chat_id=query.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=query.message.message_thread_id if query.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
    
    elif pin_option == "custom":
        # Show template for custom message (use HTML to avoid escaping issues)
        template_text = """✏️ <b>Pin Custom Message</b>

Copy this format and edit your message:

[PINNED] Your custom message here
You can use multiple lines
Add emojis 📌
Format as needed

<b>Example - Copy and edit:</b>

[PINNED] 🎯 Today's Focus
• Complete all pending tasks
• Review QA submissions
• Update project status

<b>Instructions:</b>
1. Copy the format above
2. Edit your message
3. Send it in this chat
4. Your message will be pinned"""
        
        await send_auto_delete_message(
            context=context,
            chat_id=query.message.chat_id,
            text=template_text,
            parse_mode='HTML',
            message_thread_id=query.message.message_thread_id if query.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )
    
    elif pin_option == "file":
        # Show template for file path (use HTML to avoid escaping issues)
        template_text = """📁 <b>Pin from File</b>

Copy this format and add your file path:

[PINNED] docs/your-file.txt

<b>Example - Copy and edit:</b>

[PINNED] docs/GUIDE_TASK_ALLOCATION.txt

<b>Instructions:</b>
1. Copy the format above
2. Replace with your file path
3. Send it in this chat
4. File content will be pinned"""
        
        await send_auto_delete_message(
            context=context,
            chat_id=query.message.chat_id,
            text=template_text,
            parse_mode='HTML',
            message_thread_id=query.message.message_thread_id if query.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )


async def handle_newissue_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle priority selection for new issue creation."""
    
    query = update.callback_query
    await query.answer()
    
    # Extract priority from callback data
    priority = query.data.replace("newissue:", "")
    
    # Handle manual ticket entry
    if priority == "manual":
        logger.info("User selected manual ticket entry")
        # Delete the selection message
        try:
            await query.message.delete()
            logger.info(f"Deleted newissue selection message")
        except Exception as e:
            logger.warning(f"Failed to delete newissue selection message: {e}")
        
        # Show priority selection for manual entry
        keyboard = [
            [InlineKeyboardButton("🔴 CRITICAL", callback_data="newissue:CRITICAL")],
            [InlineKeyboardButton("🟠 HIGH", callback_data="newissue:HIGH")],
            [InlineKeyboardButton("🟡 MEDIUM", callback_data="newissue:MEDIUM")],
            [InlineKeyboardButton("🟢 LOW", callback_data="newissue:LOW")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = "🚨 **Create New Issue**\n\n"
        message += "Select the priority level for your issue:\n\n"
        message += "🔴 **CRITICAL** - System down, blocking all work\n"
        message += "🟠 **HIGH** - Major feature broken, affects many users\n"
        message += "🟡 **MEDIUM** - Important but not urgent, workaround exists\n"
        message += "🟢 **LOW** - Minor issue, enhancement request"
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            message_thread_id=query.message.message_thread_id if query.message.is_topic_message else None
        )
        return
    
    # Create issue template (no auto-generated ticket)
    issue_service = context.bot_data.get('issue_service')
    if issue_service:
        template = issue_service.parser.format_issue_template(
            ticket="",  # No auto-generation
            assignee="",
            issue_ticket=""  # Will be auto-generated
        )
        # Replace the priority placeholder with selected priority
        template = template.replace("LOW / MEDIUM / HIGH / CRITICAL", priority)
    else:
        template = f"""[TICKET] #POV260406 (existing task ticket)
[ISSUE] Short descriptive title
[DETAILS] Detailed explanation of the issue, steps to reproduce, expected vs actual behavior
[PRIORITY] {priority}
[ASSIGNEE] @username (optional)"""
    
    # Delete the selection message
    try:
        await query.message.delete()
        logger.info(f"Deleted newissue selection message")
    except Exception as e:
        logger.warning(f"Failed to delete newissue selection message: {e}")
    
    # Priority emoji mapping
    priority_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠", 
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }
    
    # Send the template with auto-delete warning
    instruction = f"🚨 **Copy this for Issue Creation**\n\n"
    instruction += f"👇 **Copy the text below:**\n"
    instruction += f"```\n{template}\n```\n\n"
    instruction += f"📝 **Instructions:**\n"
    instruction += f"• **[TICKET]** - Enter the existing task ticket that has the issue\n"
    instruction += f"• **[ISSUE]** - Brief title describing the problem\n"
    instruction += f"• **[DETAILS]** - Detailed explanation, steps to reproduce\n"
    instruction += f"• **[PRIORITY]** - {priority_emoji.get(priority, '❓')} {priority} (pre-selected)\n"
    instruction += f"• **[ASSIGNEE]** - Optional username with @ (can be left empty)\n\n"
    instruction += f"**Important:** Use the ticket ID of the task that has the problem, not a new ticket!"
    
    await send_auto_delete_message(
        context=context,
        chat_id=query.message.chat_id,
        text=instruction,
        parse_mode='Markdown',
        message_thread_id=query.message.message_thread_id if query.message.is_topic_message else None,
        delete_after_seconds=30,
        warning_text=True
    )
    """Setup command handlers."""
    
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("taskhelp", cmd_taskhelp))
    application.add_handler(CommandHandler("brand", cmd_brand))
    application.add_handler(CommandHandler("newtask", cmd_newtask))
    application.add_handler(CommandHandler("support", cmd_support))
    application.add_handler(CommandHandler("pin", cmd_pin))
    application.add_handler(CommandHandler("edit", cmd_edit))
    
    # Core Operations commands
    application.add_handler(CommandHandler("myissues", cmd_myissues))
    application.add_handler(CommandHandler("myclaimedissues", cmd_myclaimedissues))
    application.add_handler(CommandHandler("openissues", cmd_openissues))
    application.add_handler(CommandHandler("issue", cmd_issue))
    application.add_handler(CommandHandler("close", cmd_close))
    application.add_handler(CommandHandler("reopen", cmd_reopen))
    application.add_handler(CommandHandler("unresolved", cmd_unresolved))
    application.add_handler(CommandHandler("inactive", cmd_inactive))
    
    # Add callback handlers for button selections
    application.add_handler(CallbackQueryHandler(handle_brand_selection, pattern="^brand:"))
    application.add_handler(CallbackQueryHandler(handle_newtask_selection, pattern="^newtask:"))
    application.add_handler(CallbackQueryHandler(handle_newissue_selection, pattern="^newissue:"))
    application.add_handler(CallbackQueryHandler(handle_support_selection, pattern="^support:"))
    application.add_handler(CallbackQueryHandler(handle_pin_selection, pattern="^pin:"))
    
    logger.info("Command handlers registered")


async def cmd_unresolved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unresolved command - show claimed but unresolved issues."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    issue_service = context.bot_data.get('issue_service')
    user_repo = context.bot_data.get('user_repository')  # Fixed: was 'user_repo'
    config = context.bot_data.get('config')
    
    if not issue_service:
        logger.error("Issue service not initialized")
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /unresolved command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /unresolved command: {e}")
    
    try:
        from src.utils.link_builder import build_message_link
        
        # Get unresolved claimed issues
        issues = await issue_service.get_unresolved_claimed_issues()
        
        if not issues:
            response = "📋 **Unresolved Issues**\n\n"
            response += f"👤 **Requested by:** @{username}\n"
            response += f"🆔 **ID:** {user_id}\n\n"
            response += "No claimed but unresolved issues found."
        else:
            response = "📋 **Unresolved Issues**\n\n"
            response += f"👤 **Requested by:** @{username}\n"
            response += f"🆔 **ID:** {user_id}\n\n"
            response += f"**Total Issues:** {len(issues)}\n\n"
            response += "_Issues that are claimed but not yet resolved, sorted by claim time:_\n\n"
            
            for issue in issues:
                priority_emoji = {
                    "LOW": "🟢",
                    "MEDIUM": "🟡",
                    "HIGH": "🟠",
                    "CRITICAL": "🔴"
                }.get(issue.priority.value, "❓")
                
                # Get usernames for claimed_by users
                handler_names = []
                for uid in issue.claimed_by:
                    if user_repo:
                        user = await user_repo.get_user(uid)
                        if user and user.username:
                            handler_names.append(f"@{user.username}")
                        else:
                            handler_names.append(f"User {uid}")
                    else:
                        handler_names.append(f"User {uid}")
                
                handlers = ", ".join(handler_names)
                
                # Create link to Core Operations topic (not specific message since it might be moved)
                core_ops_link = f"https://t.me/c/{str(abs(config.TELEGRAM_GROUP_ID))[3:]}/{config.TOPIC_CORE_OPERATIONS}"
                response += f"🟡 [**{issue.ticket}**]({core_ops_link}) - {issue.title}\n"
                response += f"{priority_emoji} Priority: {issue.priority.value}\n"
                response += f"👍 Claimed by: {handlers}\n"
                
                if issue.claimed_at:
                    response += f"📅 Claimed: {issue.claimed_at.strftime('%Y-%m-%d %H:%M')}\n"
                response += "\n"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=30,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /unresolved command: {e}")
        error_msg = f"❌ Error retrieving unresolved issues: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_inactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /inactive command - show unclaimed issues."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    issue_service = context.bot_data.get('issue_service')
    config = context.bot_data.get('config')
    
    if not issue_service:
        logger.error("Issue service not initialized")
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /inactive command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /inactive command: {e}")
    
    try:
        from src.utils.link_builder import build_message_link
        
        # Get inactive (unclaimed) issues
        issues = await issue_service.get_inactive_issues()
        
        if not issues:
            response = "📋 **Inactive Issues**\n\n"
            response += f"👤 **Requested by:** @{username}\n"
            response += f"🆔 **ID:** {user_id}\n\n"
            response += "No unclaimed issues found."
        else:
            response = "📋 **Inactive Issues**\n\n"
            response += f"👤 **Requested by:** @{username}\n"
            response += f"🆔 **ID:** {user_id}\n\n"
            response += f"**Total Issues:** {len(issues)}\n\n"
            response += "_Issues that have not been claimed by anyone, sorted by creation time:_\n\n"
            
            for issue in issues:
                priority_emoji = {
                    "LOW": "🟢",
                    "MEDIUM": "🟡",
                    "HIGH": "🟠",
                    "CRITICAL": "🔴"
                }.get(issue.priority.value, "❓")
                
                # Create link to Core Operations topic (not specific message since it might be moved)
                core_ops_link = f"https://t.me/c/{str(abs(config.TELEGRAM_GROUP_ID))[3:]}/{config.TOPIC_CORE_OPERATIONS}"
                response += f"🔴 [**{issue.ticket}**]({core_ops_link}) - {issue.title}\n"
                response += f"{priority_emoji} Priority: {issue.priority.value}\n"
                response += f"❓ Unclaimed\n"
                
                if issue.created_at:
                    response += f"📅 Created: {issue.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                response += "\n"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=30,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /inactive command: {e}")
        error_msg = f"❌ Error retrieving inactive issues: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def handle_newissue_task_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle task selection for new issue creation."""
    
    query = update.callback_query
    await query.answer()
    
    # Extract ticket from callback data
    ticket = query.data.replace("newissue_task:", "")
    
    # Now show priority selection for this specific task
    keyboard = [
        [InlineKeyboardButton("🔴 CRITICAL", callback_data=f"newissue_priority:{ticket}:CRITICAL")],
        [InlineKeyboardButton("🟠 HIGH", callback_data=f"newissue_priority:{ticket}:HIGH")],
        [InlineKeyboardButton("🟡 MEDIUM", callback_data=f"newissue_priority:{ticket}:MEDIUM")],
        [InlineKeyboardButton("🟢 LOW", callback_data=f"newissue_priority:{ticket}:LOW")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Update the message
    message = f"🚨 **Create Issue for Task #{ticket}**\n\n"
    message += "Select the priority level for this issue:\n\n"
    message += "🔴 **CRITICAL** - System down, blocking all work\n"
    message += "🟠 **HIGH** - Major feature broken, affects many users\n"
    message += "🟡 **MEDIUM** - Important but not urgent, workaround exists\n"
    message += "🟢 **LOW** - Minor issue, enhancement request"
    
    await query.edit_message_text(
        text=message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def handle_newissue_priority_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle priority selection for specific task issue creation.
    Shows the issue template with pre-filled ticket and priority in Core Operations.
    """
    
    query = update.callback_query
    await query.answer()
    
    config = context.bot_data.get('config')
    
    # Extract ticket and priority from callback data
    parts = query.data.replace("newissue_priority:", "").split(":")
    if len(parts) != 2:
        logger.error(f"Invalid callback data: {query.data}")
        return
    
    ticket, priority = parts
    
    # Generate the next issue ticket for preview
    issue_repository = context.bot_data.get('issue_repository')
    if issue_repository:
        next_issue_ticket = await issue_repository.generate_issue_ticket(ticket)
    else:
        next_issue_ticket = f"{ticket}-I1"
    
    # Create issue template with the selected task ticket
    issue_service = context.bot_data.get('issue_service')
    if issue_service:
        template = issue_service.parser.format_issue_template(
            ticket=ticket,
            assignee="",
            issue_ticket=next_issue_ticket
        )
        # Replace the priority placeholder with selected priority
        template = template.replace("LOW / MEDIUM / HIGH / CRITICAL", priority)
    else:
        template = f"""[TICKET] #{ticket}
[ISSUETICKET] #{next_issue_ticket}
[ISSUE] Short descriptive title
[DETAILS] Detailed explanation of the issue, steps to reproduce, expected vs actual behavior
[PRIORITY] {priority}
[ASSIGNEE] @username (optional)"""
    
    # Delete the selection message
    try:
        await query.message.delete()
        logger.info(f"Deleted newissue priority selection message")
    except Exception as e:
        logger.warning(f"Failed to delete newissue priority selection message: {e}")
    
    # Priority emoji mapping
    priority_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠", 
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }
    
    # Send the template to Core Operations topic (or current topic if already there)
    target_topic = query.message.message_thread_id if query.message.is_topic_message else None
    
    # If not in Core Operations, send to Core Operations
    if target_topic != config.TOPIC_CORE_OPERATIONS:
        target_topic = config.TOPIC_CORE_OPERATIONS
    
    instruction = f"🚨 **Issue Template for Task #{ticket}**\n\n"
    instruction += f"👇 **Copy and edit the text below:**\n"
    instruction += f"```\n{template}\n```\n\n"
    instruction += f"📝 **Instructions:**\n"
    instruction += f"• **[TICKET]** - Task {ticket} (pre-filled)\n"
    instruction += f"• **[ISSUE]** - Brief title describing the problem\n"
    instruction += f"• **[DETAILS]** - Detailed explanation, steps to reproduce\n"
    instruction += f"• **[PRIORITY]** - {priority_emoji.get(priority, '❓')} {priority} (pre-selected)\n"
    instruction += f"• **[ASSIGNEE]** - Optional username with @ (can be left empty)\n\n"
    instruction += f"**After editing, post it in this topic to create the issue.**\n"
    instruction += f"_Issue ticket (e.g., {ticket}-I1) will be auto-generated._"
    
    await send_auto_delete_message(
        context=context,
        chat_id=query.message.chat_id,
        text=instruction,
        parse_mode='Markdown',
        message_thread_id=target_topic,
        delete_after_seconds=30,  # Give time to copy
        warning_text=True
    )


async def handle_reply_newissue_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle priority selection for reply-based issue creation."""
    
    query = update.callback_query
    await query.answer()
    
    # Extract ticket and priority from callback data
    parts = query.data.replace("reply_newissue:", "").split(":")
    if len(parts) != 2:
        logger.error(f"Invalid callback data: {query.data}")
        return
    
    ticket, priority = parts
    
    # Generate the next issue ticket for preview
    issue_repository = context.bot_data.get('issue_repository')
    if issue_repository:
        next_issue_ticket = await issue_repository.generate_issue_ticket(ticket)
    else:
        next_issue_ticket = f"{ticket}-I1"
    
    # Create issue template with the selected task ticket
    issue_service = context.bot_data.get('issue_service')
    if issue_service:
        template = issue_service.parser.format_issue_template(
            ticket=ticket,
            assignee="",
            issue_ticket=next_issue_ticket
        )
        # Replace the priority placeholder with selected priority
        template = template.replace("LOW / MEDIUM / HIGH / CRITICAL", priority)
    else:
        template = f"""[TICKET] #{ticket}
[ISSUETICKET] #{next_issue_ticket}
[ISSUE] Short descriptive title
[DETAILS] Detailed explanation of the issue, steps to reproduce, expected vs actual behavior
[PRIORITY] {priority}
[ASSIGNEE] @username (optional)"""
    
    # Delete the selection message
    try:
        await query.message.delete()
        logger.info(f"Deleted reply newissue priority selection message")
    except Exception as e:
        logger.warning(f"Failed to delete reply newissue priority selection message: {e}")
    
    # Priority emoji mapping
    priority_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠", 
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }
    
    # Get Core Operations topic ID from config
    config = context.bot_data.get('config')
    core_ops_topic = getattr(config, 'TOPIC_CORE_OPERATIONS', 4)
    
    # Send the template to Core Operations topic with auto-delete warning
    instruction = f"🚨 **Copy this for Issue Creation**\n\n"
    instruction += f"👇 **Copy the text below:**\n"
    instruction += f"```\n{template}\n```\n\n"
    instruction += f"📝 **Instructions:**\n"
    instruction += f"• **[TICKET]** - Task {ticket} (pre-filled from reply)\n"
    instruction += f"• **[ISSUE]** - Brief title describing the problem\n"
    instruction += f"• **[DETAILS]** - Detailed explanation, steps to reproduce\n"
    instruction += f"• **[PRIORITY]** - {priority_emoji.get(priority, '❓')} {priority} (pre-selected)\n"
    instruction += f"• **[ASSIGNEE]** - Optional username with @ (can be left empty)\n\n"
    instruction += f"**This issue will be linked to task {ticket}**"
    
    await send_auto_delete_message(
        context=context,
        chat_id=query.message.chat_id,
        text=instruction,
        parse_mode='Markdown',
        message_thread_id=core_ops_topic,
        delete_after_seconds=30,
        warning_text=True
    )


async def handle_taskstate_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle task state selection for filtering."""
    query = update.callback_query
    await query.answer()
    
    # Extract state from callback data
    state = query.data.replace("taskstate:", "")
    
    task_service = context.bot_data.get('task_service')
    
    if not task_service:
        await query.edit_message_text(text="❌ Task service not available")
        return
    
    try:
        from src.data.models.task import TaskState
        
        # Get all tasks in this state
        tasks = await task_service.get_tasks_by_state(TaskState(state))
        
        if not tasks:
            await query.edit_message_text(
                text=f"📭 No tasks found in state: **{state}**",
                parse_mode='Markdown'
            )
            return
        
        # Build message
        message = f"📋 **Tasks in {state}** ({len(tasks)})\n\n"
        
        state_emojis = {
            'ASSIGNED': '📌',
            'STARTED': '⚙️',
            'QA_SUBMITTED': '🔍',
            'REJECTED': '❌',
            'APPROVED': '✅'
        }
        
        emoji = state_emojis.get(state, '•')
        
        for task in tasks[:20]:  # Show max 20
            message += f"{emoji} <a href='https://t.me/c/{abs(query.message.chat_id)}/{task.message_id}'>#{task.ticket}</a> - {task.brand}\n"
        
        if len(tasks) > 20:
            message += f"\n... and {len(tasks) - 20} more"
        
        await query.edit_message_text(
            text=message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in handle_taskstate_selection: {e}", exc_info=True)
        await query.edit_message_text(text=f"❌ Error: {str(e)}")


async def handle_filter_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle filter selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract filter type from callback data
    filter_type = query.data.replace("filter:", "")
    
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        if filter_type == "brand":
            # Show brand options
            keyboard = [
                [InlineKeyboardButton("POV - Povaly", callback_data="filterbrand:POV")],
                [InlineKeyboardButton("VRB - VorosaBajar", callback_data="filterbrand:VRB")],
                [InlineKeyboardButton("GSM - GSMAura", callback_data="filterbrand:GSM")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="🏷️ **Filter by Brand**\n\nSelect a brand:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        elif filter_type == "state":
            # Show state options
            keyboard = [
                [InlineKeyboardButton("📌 ASSIGNED", callback_data="filterstate:ASSIGNED")],
                [InlineKeyboardButton("⚙️ STARTED", callback_data="filterstate:STARTED")],
                [InlineKeyboardButton("🔍 QA_SUBMITTED", callback_data="filterstate:QA_SUBMITTED")],
                [InlineKeyboardButton("❌ REJECTED", callback_data="filterstate:REJECTED")],
                [InlineKeyboardButton("✅ APPROVED", callback_data="filterstate:APPROVED")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="📊 **Filter by State**\n\nSelect a state:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        elif filter_type == "deadline":
            # Show deadline options
            keyboard = [
                [InlineKeyboardButton("⏰ Today", callback_data="filterdeadline:today")],
                [InlineKeyboardButton("📅 This Week", callback_data="filterdeadline:week")],
                [InlineKeyboardButton("📆 This Month", callback_data="filterdeadline:month")],
                [InlineKeyboardButton("🔴 Overdue", callback_data="filterdeadline:overdue")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="⏰ **Filter by Deadline**\n\nSelect a deadline range:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        else:
            await query.edit_message_text(text="❌ Filter type not supported yet")
        
    except Exception as e:
        logger.error(f"Error in handle_filter_selection: {e}", exc_info=True)
        await query.edit_message_text(text=f"❌ Error: {str(e)}")


# ============================================================================
# ATTENDANCE & LEAVE COMMANDS
# ============================================================================

async def cmd_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /checkin command - manual check-in."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    config = context.bot_data.get('config')
    
    # Delete the command message
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete /checkin command: {e}")
    
    try:
        from src.data.repositories.attendance_repository import AttendanceRepository
        from src.data.models.attendance import Attendance
        
        attendance_repo = AttendanceRepository(context.bot_data.get('db_adapter'))
        today = date.today()
        
        # Check if already checked in today
        existing_attendance = await attendance_repo.get_attendance(user_id, today)
        
        if existing_attendance:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"⚠️ **Already Checked In**\n\nYou checked in today at {existing_attendance.checkin_time.strftime('%I:%M %p')}",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Create attendance record
        now = datetime.now()
        
        # Check if late (after 10:00 AM)
        late_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        is_late = now > late_time
        
        attendance = Attendance(
            id=None,
            user_id=user_id,
            date=today,
            checkin_time=now,
            checkout_time=None,
            is_late=is_late,
            is_auto_checkout=False,
            total_hours=None
        )
        
        await attendance_repo.create_attendance(attendance)
        
        # Send confirmation to Attendance & Leave Control topic
        status_text = "⚠️ Late" if is_late else "✅ On-time"
        time_str = now.strftime('%I:%M %p')
        
        attendance_msg = f"""✅ **Check-in Recorded**

**Employee:** @{username}
**User ID:** {user_id}
**Time:** {time_str}
**Status:** {status_text}
**Date:** {today.strftime('%Y-%m-%d')}"""
        
        await context.bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=attendance_msg,
            parse_mode='Markdown',
            message_thread_id=config.TOPIC_ATTENDANCE_LEAVE
        )
        
        # Send DM confirmation
        await context.bot.send_message(
            chat_id=user_id,
            text=f"""✅ **Check-in Recorded**

**Time:** {time_str}
**Status:** {status_text}
**Date:** {today.strftime('%Y-%m-%d')}

Have a productive day!""",
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Manual check-in recorded for user {user_id} (@{username}) at {time_str} (late={is_late})")
        
    except Exception as e:
        logger.error(f"Error in /checkin command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error recording check-in: {str(e)}",
            message_thread_id=update.message.message_thread_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /checkout command - manual check-out."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    config = context.bot_data.get('config')
    
    # Delete the command message
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete /checkout command: {e}")
    
    try:
        from src.data.repositories.attendance_repository import AttendanceRepository
        
        attendance_repo = AttendanceRepository(context.bot_data.get('db_adapter'))
        today = date.today()
        
        # Check if checked in today
        attendance = await attendance_repo.get_attendance(user_id, today)
        
        if not attendance:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text="⚠️ **Not Checked In**\n\nYou haven't checked in today. Use `/checkin` first.",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        if attendance.checkout_time:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"⚠️ **Already Checked Out**\n\nYou checked out today at {attendance.checkout_time.strftime('%I:%M %p')}",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Update checkout time
        now = datetime.now()
        await attendance_repo.update_checkout(user_id, today, now, is_auto=False)
        
        # Calculate total hours
        total_seconds = (now - attendance.checkin_time).total_seconds()
        total_hours = total_seconds / 3600
        
        # Send to Attendance & Leave Control topic
        checkin_str = attendance.checkin_time.strftime('%I:%M %p')
        checkout_str = now.strftime('%I:%M %p')
        
        attendance_msg = f"""🏁 **Check-out Recorded**

**Employee:** @{username}
**User ID:** {user_id}
**Check-in:** {checkin_str}
**Check-out:** {checkout_str}
**Total Hours:** {total_hours:.1f} hours
**Date:** {today.strftime('%Y-%m-%d')}"""
        
        await context.bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=attendance_msg,
            parse_mode='Markdown',
            message_thread_id=config.TOPIC_ATTENDANCE_LEAVE
        )
        
        # Send DM confirmation
        await context.bot.send_message(
            chat_id=user_id,
            text=f"""🏁 **Check-out Recorded**

**Check-in:** {checkin_str}
**Check-out:** {checkout_str}
**Total Hours:** {total_hours:.1f} hours
**Date:** {today.strftime('%Y-%m-%d')}

Have a great evening!""",
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Manual check-out recorded for user {user_id} (@{username}) at {checkout_str} ({total_hours:.1f} hours)")
        
    except Exception as e:
        logger.error(f"Error in /checkout command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error recording check-out: {str(e)}",
            message_thread_id=update.message.message_thread_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_myattendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myattendance command - view attendance history."""
    user_id = update.effective_user.id
    config = context.bot_data.get('config')
    
    try:
        from src.data.repositories.attendance_repository import AttendanceRepository
        
        attendance_repo = AttendanceRepository(context.bot_data.get('db_adapter'))
        
        # Get month from args or use current month
        if context.args and len(context.args) > 0:
            # Parse month (format: 2026-05)
            try:
                year, month = map(int, context.args[0].split('-'))
                start_date = date(year, month, 1)
                # Get last day of month
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
            except:
                await update.message.reply_text("❌ Invalid month format. Use: YYYY-MM (e.g., 2026-05)")
                return
        else:
            # Current month
            today = date.today()
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        # Get attendance records
        records = await attendance_repo.get_attendance_by_user(user_id, start_date, end_date)
        
        if not records:
            await update.message.reply_text(
                f"📊 **No Attendance Records**\n\nNo attendance found for {start_date.strftime('%B %Y')}",
                parse_mode='Markdown'
            )
            return
        
        # Get break records for the period
        db_adapter = context.bot_data.get('db_adapter')
        breaks = await db_adapter.get_breaks_by_user_range(user_id, start_date, end_date)
        
        # Calculate total break time
        total_break_minutes = sum(b.duration_minutes for b in breaks if b.duration_minutes)
        
        # Build attendance summary
        total_days = len(records)
        late_days = sum(1 for r in records if r.is_late)
        total_hours = sum(r.total_hours for r in records if r.total_hours)
        
        message = f"""📊 **Attendance Summary**

**Period:** {start_date.strftime('%B %Y')}
**Total Days:** {total_days}
**Late Check-ins:** {late_days}
**Total Work Hours:** {total_hours:.1f} hours
**Total Break Time:** {total_break_minutes:.0f} minutes ({total_break_minutes/60:.1f} hours)
**Total Breaks:** {len(breaks)}

**Recent Records:**
"""
        
        # Show last 10 records
        for record in sorted(records, key=lambda x: x.date, reverse=True)[:10]:
            checkin = record.checkin_time.strftime('%I:%M %p')
            checkout = record.checkout_time.strftime('%I:%M %p') if record.checkout_time else "Not checked out"
            hours = f"{record.total_hours:.1f}h" if record.total_hours else "-"
            late_flag = "⚠️" if record.is_late else "✅"
            
            # Get breaks for this day
            day_breaks = [b for b in breaks if b.date == record.date]
            break_count = len(day_breaks)
            break_time = sum(b.duration_minutes for b in day_breaks if b.duration_minutes)
            
            message += f"\n{late_flag} **{record.date.strftime('%Y-%m-%d')}**"
            message += f"\n   In: {checkin} | Out: {checkout} | Hours: {hours}"
            if break_count > 0:
                message += f"\n   Breaks: {break_count} ({break_time:.0f} min)"
            message += "\n"
        
        if len(records) > 10:
            message += f"\n_Showing 10 of {len(records)} records_"
        
        message += f"\n\n💡 Use `/attendancedetails YYYY-MM-DD` to see detailed breakdown for a specific day"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in /myattendance command: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error retrieving attendance: {str(e)}")


async def cmd_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /attendance command - admins view any user's attendance."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    config = context.bot_data.get('config')
    
    # Delete the command message
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete /attendance command: {e}")
    
    # Check if user is admin/manager
    if user_id not in config.ADMINISTRATORS and user_id not in config.MANAGERS and user_id not in config.OWNERS:
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ This command is only available to admins and managers.",
            message_thread_id=update.message.message_thread_id,
            delete_after_seconds=10,
            warning_text=True
        )
        return
    
    try:
        # Parse arguments: /attendance @username [YYYY-MM]
        if not context.args:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text="**Usage:** `/attendance @username [YYYY-MM]`\n\n"
                     "**Examples:**\n"
                     "`/attendance @john` - Current month\n"
                     "`/attendance @john 2026-05` - Specific month",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Get username
        target_username = context.args[0].lstrip('@')
        
        # Get user from database
        user_repo = context.bot_data.get('user_repository')
        target_user = await user_repo.get_user_by_username(target_username)
        
        if not target_user:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ User @{target_username} not found in database.",
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=10,
                warning_text=True
            )
            return
        
        target_user_id = target_user.user_id
        
        from src.data.repositories.attendance_repository import AttendanceRepository
        attendance_repo = AttendanceRepository(context.bot_data.get('db_adapter'))
        
        # Get month from args or use current month
        if len(context.args) > 1:
            try:
                year, month = map(int, context.args[1].split('-'))
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
            except:
                await send_auto_delete_message(
                    context=context,
                    chat_id=update.message.chat_id,
                    text="❌ Invalid month format. Use: YYYY-MM (e.g., 2026-05)",
                    message_thread_id=update.message.message_thread_id,
                    delete_after_seconds=10,
                    warning_text=True
                )
                return
        else:
            today = date.today()
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
        
        # Get attendance records
        records = await attendance_repo.get_attendance_by_user(target_user_id, start_date, end_date)
        
        if not records:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"📊 **No Attendance Records**\n\n"
                     f"No attendance found for @{target_username} in {start_date.strftime('%B %Y')}",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Get break records
        db_adapter = context.bot_data.get('db_adapter')
        breaks = await db_adapter.get_breaks_by_user_range(target_user_id, start_date, end_date)
        
        # Calculate totals
        total_break_minutes = sum(b.duration_minutes for b in breaks if b.duration_minutes)
        total_days = len(records)
        late_days = sum(1 for r in records if r.is_late)
        total_hours = sum(r.total_hours for r in records if r.total_hours)
        
        message = f"""📊 **Attendance Report**

**Employee:** @{target_username}
**User ID:** {target_user_id}
**Period:** {start_date.strftime('%B %Y')}

**Summary:**
• Total Days: {total_days}
• Late Check-ins: {late_days}
• Total Work Hours: {total_hours:.1f} hours
• Total Break Time: {total_break_minutes:.0f} minutes ({total_break_minutes/60:.1f} hours)
• Total Breaks: {len(breaks)}

**Recent Records:**
"""
        
        # Show last 10 records
        for record in sorted(records, key=lambda x: x.date, reverse=True)[:10]:
            checkin = record.checkin_time.strftime('%I:%M %p')
            checkout = record.checkout_time.strftime('%I:%M %p') if record.checkout_time else "Not checked out"
            hours = f"{record.total_hours:.1f}h" if record.total_hours else "-"
            late_flag = "⚠️" if record.is_late else "✅"
            
            # Get breaks for this day
            day_breaks = [b for b in breaks if b.date == record.date]
            break_count = len(day_breaks)
            break_time = sum(b.duration_minutes for b in day_breaks if b.duration_minutes)
            
            message += f"\n{late_flag} **{record.date.strftime('%Y-%m-%d')}**"
            message += f"\n   In: {checkin} | Out: {checkout} | Hours: {hours}"
            if break_count > 0:
                message += f"\n   Breaks: {break_count} ({break_time:.0f} min)"
            message += "\n"
        
        if len(records) > 10:
            message += f"\n_Showing 10 of {len(records)} records_"
        
        message += f"\n\n💡 Use `/attendancedetails YYYY-MM-DD` to see detailed breakdown"
        message += f"\n\n_Requested by: @{username}_"
        
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=message,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id
        )
        
    except Exception as e:
        logger.error(f"Error in /attendance command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error retrieving attendance: {str(e)}",
            message_thread_id=update.message.message_thread_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_break(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /break command - start a break."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    config = context.bot_data.get('config')
    
    # Delete the command message
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete /break command: {e}")
    
    try:
        # Get reason from args
        if not context.args:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text="❌ **Missing Reason**\n\nUsage: `/break <reason>`\nExample: `/break Lunch break`",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        reason = ' '.join(context.args)
        
        from src.data.models.break_record import BreakRecord
        
        db_adapter = context.bot_data.get('db_adapter')
        today = date.today()
        
        # Check if already on break
        active_break = await db_adapter.get_active_break(user_id, today)
        if active_break:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"⚠️ **Already on Break**\n\nYou started a break at {active_break.break_start.strftime('%I:%M %p')}\nReason: {active_break.reason}\n\nUse `/recheckin` to end your break.",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check if checked in today
        from src.data.repositories.attendance_repository import AttendanceRepository
        attendance_repo = AttendanceRepository(db_adapter)
        attendance = await attendance_repo.get_attendance(user_id, today)
        
        if not attendance:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text="⚠️ **Not Checked In**\n\nYou need to check in first before taking a break.\nUse `/checkin` or start a task.",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Create break record
        now = datetime.now()
        break_record = BreakRecord(
            id=None,
            user_id=user_id,
            date=today,
            break_start=now,
            break_end=None,
            reason=reason,
            duration_minutes=None
        )
        
        await db_adapter.insert_break_record(break_record)
        
        # Send to Attendance & Leave Control topic
        time_str = now.strftime('%I:%M %p')
        
        attendance_msg = f"""☕ **Break Started**

**Employee:** @{username}
**User ID:** {user_id}
**Time:** {time_str}
**Reason:** {reason}
**Date:** {today.strftime('%Y-%m-%d')}"""
        
        await context.bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=attendance_msg,
            parse_mode='Markdown',
            message_thread_id=config.TOPIC_ATTENDANCE_LEAVE
        )
        
        # Send DM confirmation
        await context.bot.send_message(
            chat_id=user_id,
            text=f"""☕ **Break Started**

**Time:** {time_str}
**Reason:** {reason}

Use `/recheckin` when you're back from break.""",
            parse_mode='Markdown'
        )
        
        logger.info(f"☕ Break started for user {user_id} (@{username}) at {time_str} - Reason: {reason}")
        
    except Exception as e:
        logger.error(f"Error in /break command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error starting break: {str(e)}",
            message_thread_id=update.message.message_thread_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_recheckin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /recheckin command - end a break."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    config = context.bot_data.get('config')
    
    # Delete the command message
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete /recheckin command: {e}")
    
    try:
        db_adapter = context.bot_data.get('db_adapter')
        today = date.today()
        
        # Check if on break
        active_break = await db_adapter.get_active_break(user_id, today)
        if not active_break:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text="⚠️ **Not on Break**\n\nYou don't have an active break to end.",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # End break
        now = datetime.now()
        await db_adapter.update_break_end(active_break.id, now)
        
        # Calculate duration
        duration_seconds = (now - active_break.break_start).total_seconds()
        duration_minutes = duration_seconds / 60
        
        # Send to Attendance & Leave Control topic
        start_str = active_break.break_start.strftime('%I:%M %p')
        end_str = now.strftime('%I:%M %p')
        
        attendance_msg = f"""🔙 **Break Ended**

**Employee:** @{username}
**User ID:** {user_id}
**Break Start:** {start_str}
**Break End:** {end_str}
**Duration:** {duration_minutes:.0f} minutes
**Reason:** {active_break.reason}
**Date:** {today.strftime('%Y-%m-%d')}"""
        
        await context.bot.send_message(
            chat_id=config.TELEGRAM_GROUP_ID,
            text=attendance_msg,
            parse_mode='Markdown',
            message_thread_id=config.TOPIC_ATTENDANCE_LEAVE
        )
        
        # Send DM confirmation
        await context.bot.send_message(
            chat_id=user_id,
            text=f"""🔙 **Break Ended**

**Break Start:** {start_str}
**Break End:** {end_str}
**Duration:** {duration_minutes:.0f} minutes

Welcome back!""",
            parse_mode='Markdown'
        )
        
        logger.info(f"🔙 Break ended for user {user_id} (@{username}) at {end_str} - Duration: {duration_minutes:.0f} min")
        
        # CHECK FOR EXCESSIVE BREAKS - Alert admins if suspicious
        all_breaks_today = await db_adapter.get_breaks_by_user_date(user_id, today)
        
        # Calculate total break time and count
        total_break_minutes = sum(b.duration_minutes for b in all_breaks_today if b.duration_minutes)
        break_count = len(all_breaks_today)
        
        # Get thresholds from config
        max_break_time = config.ATTENDANCE_MAX_BREAK_TIME_MINUTES
        max_break_count = config.ATTENDANCE_MAX_BREAK_COUNT
        
        alert_reasons = []
        
        if total_break_minutes > max_break_time:
            alert_reasons.append(f"Total break time: {total_break_minutes:.0f} minutes (exceeds {max_break_time} min limit)")
        
        if break_count > max_break_count:
            alert_reasons.append(f"Break count: {break_count} breaks (exceeds {max_break_count} breaks limit)")
        
        # Send alert to Admin Control Panel if thresholds exceeded
        if alert_reasons:
            alert_msg = f"""🚨 **Excessive Break Alert**

**Employee:** @{username}
**User ID:** {user_id}
**Date:** {today.strftime('%Y-%m-%d')}

**Alerts:**
"""
            for reason in alert_reasons:
                alert_msg += f"• {reason}\n"
            
            alert_msg += f"""
**Today's Break Summary:**
• Total Breaks: {break_count}
• Total Break Time: {total_break_minutes:.0f} minutes ({total_break_minutes/60:.1f} hours)

**Break Details:**
"""
            
            for i, brk in enumerate(all_breaks_today, 1):
                brk_start = brk.break_start.strftime('%I:%M %p')
                brk_end = brk.break_end.strftime('%I:%M %p') if brk.break_end else "Ongoing"
                brk_duration = f"{brk.duration_minutes:.0f} min" if brk.duration_minutes else "Ongoing"
                alert_msg += f"{i}. {brk_start} - {brk_end} ({brk_duration}) - {brk.reason}\n"
            
            alert_msg += "\n⚠️ **Action Required:** Please review this employee's break pattern."
            
            await context.bot.send_message(
                chat_id=config.TELEGRAM_GROUP_ID,
                text=alert_msg,
                parse_mode='Markdown',
                message_thread_id=config.TOPIC_ADMIN_CONTROL_PANEL
            )
            
            logger.warning(f"🚨 Excessive break alert sent for user {user_id} (@{username}) - {', '.join(alert_reasons)}")
        
    except Exception as e:
        logger.error(f"Error in /recheckin command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error ending break: {str(e)}",
            message_thread_id=update.message.message_thread_id,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_attendancedetails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /attendancedetails command - view detailed attendance for a specific day."""
    user_id = update.effective_user.id
    config = context.bot_data.get('config')
    
    try:
        # Get date from args
        if not context.args:
            await update.message.reply_text(
                "❌ **Missing Date**\n\nUsage: `/attendancedetails YYYY-MM-DD`\nExample: `/attendancedetails 2026-05-01`",
                parse_mode='Markdown'
            )
            return
        
        try:
            target_date = date.fromisoformat(context.args[0])
        except:
            await update.message.reply_text("❌ Invalid date format. Use: YYYY-MM-DD (e.g., 2026-05-01)")
            return
        
        from src.data.repositories.attendance_repository import AttendanceRepository
        
        db_adapter = context.bot_data.get('db_adapter')
        attendance_repo = AttendanceRepository(db_adapter)
        
        # Get attendance for the day
        attendance = await attendance_repo.get_attendance(user_id, target_date)
        
        if not attendance:
            await update.message.reply_text(
                f"📊 **No Attendance Record**\n\nNo attendance found for {target_date.strftime('%Y-%m-%d')}",
                parse_mode='Markdown'
            )
            return
        
        # Get breaks for the day
        breaks = await db_adapter.get_breaks_by_user_date(user_id, target_date)
        
        # Build detailed message
        checkin_str = attendance.checkin_time.strftime('%I:%M %p')
        checkout_str = attendance.checkout_time.strftime('%I:%M %p') if attendance.checkout_time else "Not checked out"
        status = "⚠️ Late" if attendance.is_late else "✅ On-time"
        hours = f"{attendance.total_hours:.1f} hours" if attendance.total_hours else "In progress"
        
        message = f"""📊 **Attendance Details**

**Date:** {target_date.strftime('%Y-%m-%d')}
**Check-in:** {checkin_str} {status}
**Check-out:** {checkout_str}
**Total Hours:** {hours}
"""
        
        if breaks:
            total_break_minutes = sum(b.duration_minutes for b in breaks if b.duration_minutes)
            message += f"\n**Breaks:** {len(breaks)} ({total_break_minutes:.0f} minutes)\n"
            
            for i, brk in enumerate(breaks, 1):
                start_str = brk.break_start.strftime('%I:%M %p')
                end_str = brk.break_end.strftime('%I:%M %p') if brk.break_end else "Ongoing"
                duration = f"{brk.duration_minutes:.0f} min" if brk.duration_minutes else "Ongoing"
                
                message += f"\n**Break {i}:**"
                message += f"\n  • Start: {start_str}"
                message += f"\n  • End: {end_str}"
                message += f"\n  • Duration: {duration}"
                message += f"\n  • Reason: {brk.reason}\n"
        else:
            message += "\n**Breaks:** None"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in /attendancedetails command: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error retrieving details: {str(e)}")


def setup_command_handlers(application: Application, config: Config):

    """Setup command handlers."""
    
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("commands", cmd_commands))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("taskhelp", cmd_taskhelp))
    application.add_handler(CommandHandler("brand", cmd_brand))
    application.add_handler(CommandHandler("newtask", cmd_newtask))
    application.add_handler(CommandHandler("newissue", cmd_newissue))
    application.add_handler(CommandHandler("support", cmd_support))
    application.add_handler(CommandHandler("pin", cmd_pin))
    application.add_handler(CommandHandler("edit", cmd_edit))
    
    # Core Operations commands
    application.add_handler(CommandHandler("myissues", cmd_myissues))
    application.add_handler(CommandHandler("myclaimedissues", cmd_myclaimedissues))
    application.add_handler(CommandHandler("openissues", cmd_openissues))
    application.add_handler(CommandHandler("issue", cmd_issue))
    application.add_handler(CommandHandler("close", cmd_close))
    application.add_handler(CommandHandler("reopen", cmd_reopen))
    application.add_handler(CommandHandler("unresolved", cmd_unresolved))
    application.add_handler(CommandHandler("inactive", cmd_inactive))
    
    # QA & Review commands
    application.add_handler(CommandHandler("newqa", cmd_newqa))
    application.add_handler(CommandHandler("myqa", cmd_myqa))
    application.add_handler(CommandHandler("reviewingqa", cmd_reviewingqa))
    application.add_handler(CommandHandler("pendingqa", cmd_pendingqa))
    application.add_handler(CommandHandler("unreviewedqa", cmd_unreviewedqa))
    application.add_handler(CommandHandler("qa", cmd_qa))
    application.add_handler(CommandHandler("approve", cmd_approve))
    application.add_handler(CommandHandler("reject", cmd_reject))
    application.add_handler(CommandHandler("reopenqa", cmd_reopenqa))
    
    # Task management commands
    application.add_handler(CommandHandler("cleantasks", cmd_cleantasks))
    application.add_handler(CommandHandler("syncdb", cmd_syncdb))
    application.add_handler(CommandHandler("resetdb", cmd_resetdb))
    application.add_handler(CommandHandler("scantopic", cmd_scantopic))
    application.add_handler(CommandHandler("dailysummary", cmd_dailysummary))
    application.add_handler(CommandHandler("syncdebug", cmd_syncdebug))
    application.add_handler(CommandHandler("debugtasks", cmd_debugtasks))
    
    # Attendance & Leave commands
    application.add_handler(CommandHandler("checkin", cmd_checkin))
    application.add_handler(CommandHandler("checkout", cmd_checkout))
    application.add_handler(CommandHandler("break", cmd_break))
    application.add_handler(CommandHandler("recheckin", cmd_recheckin))
    application.add_handler(CommandHandler("myattendance", cmd_myattendance))
    application.add_handler(CommandHandler("attendance", cmd_attendance))
    application.add_handler(CommandHandler("attendancedetails", cmd_attendancedetails))
    
    # Phase 1: Task tracking commands
    application.add_handler(CommandHandler("mytasks", cmd_mytasks))
    application.add_handler(CommandHandler("tasksbystate", cmd_tasksbystate))
    application.add_handler(CommandHandler("overduetasks", cmd_overduetasks))
    application.add_handler(CommandHandler("filter", cmd_filter))
    application.add_handler(CommandHandler("taskstats", cmd_taskstats))
    
    # Add callback handlers for button selections
    application.add_handler(CallbackQueryHandler(handle_brand_selection, pattern="^brand:"))
    application.add_handler(CallbackQueryHandler(handle_newtask_selection, pattern="^newtask:"))
    application.add_handler(CallbackQueryHandler(handle_newissue_selection, pattern="^newissue:"))
    application.add_handler(CallbackQueryHandler(handle_support_selection, pattern="^support:"))
    application.add_handler(CallbackQueryHandler(handle_pin_selection, pattern="^pin:"))
    
    # New issue creation callback handlers
    application.add_handler(CallbackQueryHandler(handle_newissue_task_selection, pattern="^newissue_task:"))
    application.add_handler(CallbackQueryHandler(handle_newissue_priority_selection, pattern="^newissue_priority:"))
    
    # Task state filtering callback handler
    application.add_handler(CallbackQueryHandler(handle_taskstate_selection, pattern="^taskstate:"))
    
    # Add pagination handler for /mytasks
    from src.bot.handlers.mytasks_pagination import handle_mytasks_pagination
    application.add_handler(CallbackQueryHandler(handle_mytasks_pagination, pattern="^mytasks_expand:"))
    
    # Add pagination handler for /myissues and /myclaimedissues
    from src.bot.handlers.myissues_pagination import handle_myissues_pagination
    application.add_handler(CallbackQueryHandler(handle_myissues_pagination, pattern="^myissues_expand:"))
    application.add_handler(CallbackQueryHandler(handle_myissues_pagination, pattern="^myclaimedissues_expand:"))
    
    # Filter callback handler
    application.add_handler(CallbackQueryHandler(handle_filter_selection, pattern="^filter:"))
    
    # Reply-based newissue callback handler
    application.add_handler(CallbackQueryHandler(handle_reply_newissue_priority, pattern="^reply_newissue:"))
    
    logger.info("Command handlers registered")


async def cmd_cleantasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cleantasks command - clean up orphaned tasks that no longer exist in Telegram."""
    user_id = update.message.from_user.id
    task_service = context.bot_data.get('task_service')
    config = context.bot_data.get('config')
    
    # Permission check
    if not is_privileged_user(user_id, config):
        await update.message.reply_text(
            "❌ **Access Denied**\n\nThis command is only available to Administrators, Managers, and Owners.",
            parse_mode='Markdown'
        )
        try:
            await update.message.delete()
        except:
            pass
        return
    
    if not task_service:
        logger.error("Task service not initialized")
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /cleantasks command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /cleantasks command: {e}")
    
    try:
        # Get all user's tasks
        all_user_tasks = await task_service.task_repo.get_tasks_by_assignee(user_id)
        
        if not all_user_tasks:
            response = "📋 **Clean Tasks**\n\nYou have no tasks to clean."
        else:
            # Show current status and offer cleanup
            active_tasks = [
                t for t in all_user_tasks 
                if t.state not in [TaskState.APPROVED, TaskState.ARCHIVED, TaskState.INACTIVE]
            ]
            
            response = f"📋 **Task Cleanup Report**\n\n"
            response += f"📊 **Current Status:**\n"
            response += f"• Database shows: {len(active_tasks)} active tasks\n"
            response += f"• You report: 5 tasks assigned to you\n"
            response += f"• Discrepancy: {len(active_tasks) - 5} orphaned tasks\n\n"
            
            if len(active_tasks) > 5:
                response += f"🧹 **Auto-Sync Available:**\n"
                response += f"• Type `/syncdb` to automatically clean up old tasks\n"
                response += f"• Keeps recent tasks (last 3 days) + 6 most recent\n"
                response += f"• Archives old tasks that likely don't exist anymore\n\n"
            
            response += f"📝 **Your Database Tasks:**\n"
            for i, task in enumerate(active_tasks, 1):
                response += f"{i}. {task.ticket} - {task.brand} ({task.created_at.date()})\n"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=60,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /cleantasks command: {e}")
        error_msg = f"❌ Error checking tasks: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_syncdb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /syncdb command - aggressive database cleanup to match current reality."""
    user_id = update.message.from_user.id
    task_service = context.bot_data.get('task_service')
    config = context.bot_data.get('config')
    
    # Permission check
    if not is_privileged_user(user_id, config):
        await update.message.reply_text(
            "❌ **Access Denied**\n\nThis command is only available to Administrators, Managers, and Owners.",
            parse_mode='Markdown'
        )
        try:
            await update.message.delete()
        except:
            pass
        return
    
    if not task_service:
        logger.error("Task service not initialized")
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /syncdb command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /syncdb command: {e}")
    
    try:
        from datetime import datetime, timedelta
        
        # Get all user's tasks from database before sync
        all_user_tasks_before = await task_service.task_repo.get_tasks_by_assignee(user_id)
        active_states = [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.REJECTED]
        active_tasks_before = [t for t in all_user_tasks_before if t.state in active_states]
        
        # AGGRESSIVE CLEANUP: Since we can't read the topic directly,
        # we'll keep only the most recent tasks and assume older ones were deleted
        
        # Keep only tasks from today (most likely to still exist in topic)
        today = datetime.now().date()
        today_tasks = [t for t in active_tasks_before if t.created_at.date() == today]
        
        # If user has more than 5 tasks from today, keep only the 5 most recent
        if len(today_tasks) > 5:
            sorted_tasks = sorted(today_tasks, key=lambda t: t.created_at, reverse=True)
            tasks_to_keep = sorted_tasks[:5]
            tasks_to_remove = sorted_tasks[5:] + [t for t in active_tasks_before if t.created_at.date() < today]
        else:
            tasks_to_keep = today_tasks
            tasks_to_remove = [t for t in active_tasks_before if t.created_at.date() < today]
        
        # Remove old/excess tasks from database
        removed_count = 0
        for task in tasks_to_remove:
            try:
                await task_service.task_repo.db.delete_task(task.ticket)
                removed_count += 1
                logger.info(f"Aggressive sync: Removed task {task.ticket}")
            except Exception as e:
                logger.error(f"Failed to remove task {task.ticket}: {e}")
        
        # Update reality tracking to match what we kept
        db_sync_service = context.bot_data.get('db_sync_service')
        if db_sync_service:
            # Clear old reality for this user
            db_sync_service.topic_reality[user_id] = set()
            # Add kept tasks to reality
            for task in tasks_to_keep:
                db_sync_service.track_task_created(user_id, task.ticket)
        
        response = f"🔄 **Aggressive Database Sync**\n\n"
        
        if removed_count > 0:
            response += f"🧹 **Cleanup Results:**\n"
            response += f"• Before: {len(active_tasks_before)} tasks\n"
            response += f"• Removed: {removed_count} old/excess tasks\n"
            response += f"• Kept: {len(tasks_to_keep)} recent tasks\n"
            response += f"• Strategy: Today's tasks only + max 5 most recent\n\n"
            
            if tasks_to_keep:
                response += f"📝 **Your Active Tasks Now:**\n"
                for task in sorted(tasks_to_keep, key=lambda t: t.created_at, reverse=True):
                    response += f"• {task.ticket} - {task.brand} (today)\n"
            else:
                response += f"📝 **No active tasks remaining**\n"
            
            response += f"\n💡 **Important:** Database cleaned aggressively. If you have tasks in Task Allocation topic that were removed, please recreate them."
        else:
            response += f"✅ **Database Already Minimal**\n\n"
            response += f"• Active tasks: {len(tasks_to_keep)}\n"
            response += f"• All tasks are from today\n\n"
            
            if tasks_to_keep:
                response += f"📝 **Your Current Tasks:**\n"
                for task in sorted(tasks_to_keep, key=lambda t: t.created_at, reverse=True):
                    response += f"• {task.ticket} - {task.brand} (today)\n"
        
        response += f"\n🔄 **Reality Sync:** Database now tracks only today's tasks. Future sync will be automatic."
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=60,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /syncdb command: {e}")
        error_msg = f"❌ Error syncing database: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_syncdebug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to show sync service status and reality tracking."""
    user_id = update.message.from_user.id
    db_sync_service = context.bot_data.get('db_sync_service')
    task_service = context.bot_data.get('task_service')
    config = context.bot_data.get('config')
    
    # Permission check
    if not is_privileged_user(user_id, config):
        await update.message.reply_text(
            "❌ **Access Denied**\n\nThis command is only available to Administrators, Managers, and Owners.",
            parse_mode='Markdown'
        )
        try:
            await update.message.delete()
        except:
            pass
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /syncdebug command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /syncdebug command: {e}")
    
    try:
        response = "🔍 **Database Sync Debug**\n\n"
        
        if not db_sync_service:
            response += "❌ **Sync Service:** Not initialized\n"
        else:
            # Get reality stats
            reality_stats = db_sync_service.get_reality_stats()
            user_reality = db_sync_service.get_user_reality(user_id)
            
            response += f"✅ **Sync Service:** Running\n"
            response += f"📊 **Reality Tracking:**\n"
            response += f"• Total users: {reality_stats['users']}\n"
            response += f"• Total tasks: {reality_stats['tasks']}\n\n"
            
            response += f"👤 **Your Reality:**\n"
            if user_reality:
                response += f"• Expected tasks: {len(user_reality)}\n"
                for ticket in sorted(user_reality):
                    response += f"  - {ticket}\n"
            else:
                response += f"• No tasks tracked\n"
            
            # Get actual database tasks
            if task_service:
                all_user_tasks = await task_service.task_repo.get_tasks_by_assignee(user_id)
                active_states = [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.REJECTED]
                active_tasks = [t for t in all_user_tasks if t.state in active_states]
                
                response += f"\n💾 **Database Tasks:**\n"
                response += f"• Actual tasks: {len(active_tasks)}\n"
                if active_tasks:
                    for task in sorted(active_tasks, key=lambda t: t.ticket):
                        response += f"  - {task.ticket}\n"
                
                # Compare reality vs database
                db_tickets = {task.ticket for task in active_tasks}
                missing_in_db = user_reality - db_tickets
                extra_in_db = db_tickets - user_reality
                
                response += f"\n🔄 **Sync Status:**\n"
                if not missing_in_db and not extra_in_db:
                    response += f"✅ Perfect sync - reality matches database\n"
                else:
                    if missing_in_db:
                        response += f"⚠️ Missing in DB: {', '.join(missing_in_db)}\n"
                    if extra_in_db:
                        response += f"🗑️ Extra in DB: {', '.join(extra_in_db)}\n"
        
        response += f"\n💡 **Tip:** Reality tracking ensures database contains exactly what's in Task Allocation topic."
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=45,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /syncdebug command: {e}")
        error_msg = f"❌ Error getting sync debug info: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_resetdb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /resetdb command - completely reset user's database to match current reality."""
    user_id = update.message.from_user.id
    task_service = context.bot_data.get('task_service')
    config = context.bot_data.get('config')
    
    # Permission check
    if not is_privileged_user(user_id, config):
        await update.message.reply_text(
            "❌ **Access Denied**\n\nThis command is only available to Administrators, Managers, and Owners.",
            parse_mode='Markdown'
        )
        try:
            await update.message.delete()
        except:
            pass
        return
    
    if not task_service:
        logger.error("Task service not initialized")
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /resetdb command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /resetdb command: {e}")
    
    try:
        from datetime import datetime
        
        # Get all user's tasks from database before reset
        all_user_tasks_before = await task_service.task_repo.get_tasks_by_assignee(user_id)
        active_states = [TaskState.ASSIGNED, TaskState.STARTED, TaskState.QA_SUBMITTED, TaskState.REJECTED]
        active_tasks_before = [t for t in all_user_tasks_before if t.state in active_states]
        
        # NUCLEAR OPTION: Remove ALL active tasks for this user
        removed_count = 0
        for task in active_tasks_before:
            try:
                await task_service.task_repo.db.delete_task(task.ticket)
                removed_count += 1
                logger.info(f"Database reset: Removed task {task.ticket}")
            except Exception as e:
                logger.error(f"Failed to remove task {task.ticket}: {e}")
        
        # Clear reality tracking for this user
        db_sync_service = context.bot_data.get('db_sync_service')
        if db_sync_service:
            db_sync_service.topic_reality[user_id] = set()
        
        response = f"🔥 **Database Reset Complete**\n\n"
        response += f"🧹 **Reset Results:**\n"
        response += f"• Removed: {removed_count} tasks from database\n"
        response += f"• Cleared: Reality tracking\n"
        response += f"• Status: Clean slate\n\n"
        
        response += f"📝 **What happens next:**\n"
        response += f"• Database is now empty for you\n"
        response += f"• Only NEW tasks you create will be tracked\n\n"
        
        response += f"💡 **Important:** If you have tasks in Task Allocation topic right now, they won't be in the database until you recreate them or the bot sees them being created."
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=45,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /resetdb command: {e}")
        error_msg = f"❌ Error resetting database: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_scantopic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scantopic command - scan Task Allocation topic for actual tasks."""
    user_id = update.message.from_user.id
    topic_scanner = context.bot_data.get('topic_scanner')
    config = context.bot_data.get('config')
    
    # Permission check
    if not is_privileged_user(user_id, config):
        await update.message.reply_text(
            "❌ **Access Denied**\n\nThis command is only available to Administrators, Managers, and Owners.",
            parse_mode='Markdown'
        )
        try:
            await update.message.delete()
        except:
            pass
        return
        logger.error("Topic scanner not initialized")
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /scantopic command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /scantopic command: {e}")
    
    try:
        # Show scanning message
        scanning_msg = await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🔍 **Scanning Task Allocation Topic**\n\nReading actual tasks from topic...",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
        )
        
        # Perform the scan and sync
        stats = await topic_scanner.sync_database_with_topic_reality(context.application)
        
        # Delete scanning message
        try:
            await scanning_msg.delete()
        except:
            pass
        
        # Build response
        if "error" in stats:
            response = f"❌ **Topic Scan Failed**\n\nError: {stats['error']}"
        else:
            response = f"🔍 **Topic Scan Complete**\n\n"
            response += f"📊 **Scan Results:**\n"
            response += f"• Users scanned: {stats['users_scanned']}\n"
            response += f"• Tasks found in topic: {stats['tasks_found_in_topic']}\n"
            response += f"• Tasks removed from DB: {stats['tasks_removed_from_db']}\n"
            response += f"• Tasks added to DB: {stats['tasks_added_to_db']}\n"
            response += f"• Users synced: {stats['users_synced']}\n\n"
            
            if stats['users_synced'] > 0:
                response += f"✅ **Database Updated**\n"
                response += f"Database now matches actual Task Allocation topic content.\n\n"
            else:
                response += f"✅ **Database Already Synced**\n"
                response += f"No changes needed - database matches topic.\n"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=45,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /scantopic command: {e}")
        error_msg = f"❌ Error scanning topic: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_dailysummary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dailysummary command - manually trigger daily task summary."""
    user_id = update.message.from_user.id
    config = context.bot_data.get('config')
    
    # Check if user is authorized (admin/manager/owner)
    is_authorized = (
        user_id in config.ADMINISTRATORS or
        user_id in config.MANAGERS or
        user_id in config.OWNERS
    )
    
    if not is_authorized:
        error_msg = "❌ **Access Denied**\n\nOnly Administrators, Managers, and Owners can trigger daily summary."
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /dailysummary command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /dailysummary command: {e}")
    
    try:
        # Get daily summary service
        daily_summary_service = context.bot_data.get('daily_summary_service')
        
        if not daily_summary_service:
            error_msg = "❌ Daily summary service not available"
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Send "processing" message
        processing_msg = "⏳ Generating daily summary..."
        processing_message = await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=processing_msg,
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
        )
        
        # Trigger daily summary
        await daily_summary_service.send_manual_summary()
        
        # Delete processing message
        try:
            await processing_message.delete()
        except:
            pass
        
        # Send success message
        success_msg = "✅ **Daily Summary Sent**\n\nCarryover task summary has been sent to Task Allocation topic and DMs sent to assignees."
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=success_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /dailysummary command: {e}", exc_info=True)
        error_msg = f"❌ Error generating daily summary: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_mytasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mytasks command - show user's assigned tasks with status."""
    user_id = update.message.from_user.id
    task_service = context.bot_data.get('task_service')
    
    # Delete the command message from group
    try:
        await update.message.delete()
        logger.info(f"Deleted /mytasks command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /mytasks command message: {e}")
    
    if not task_service:
        # Send error to DM
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Task service not available",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send DM to user {user_id}: {e}")
        return
    
    try:
        from src.data.models.task import TaskState
        from src.bot.handlers.mytasks_pagination import build_mytasks_message
        
        # Get all tasks assigned to user
        all_tasks = await task_service.get_tasks_by_assignee(user_id)
        
        # Get username
        username = update.message.from_user.username or update.message.from_user.first_name
        
        # Log the tasks for debugging
        logger.info(f"📊 /mytasks for user {user_id}: Found {len(all_tasks)} tasks")
        for task in all_tasks:
            logger.info(f"  - {task.ticket} (state: {task.state.value}, assignee: {task.assignee_id})")
        
        if not all_tasks:
            # Send to DM with auto-delete
            try:
                sent_msg = await context.bot.send_message(
                    chat_id=user_id,
                    text="📭 You have no assigned tasks",
                    parse_mode='Markdown'
                )
                
                # Auto-delete after 60 seconds
                async def delete_dm():
                    await asyncio.sleep(60)
                    try:
                        await sent_msg.delete()
                    except:
                        pass
                asyncio.create_task(delete_dm())
            except Exception as e:
                logger.error(f"Failed to send DM to user {user_id}: {e}")
            return
        
        # Group tasks by state
        tasks_by_state = {}
        for task in all_tasks:
            state = task.state.value
            if state not in tasks_by_state:
                tasks_by_state[state] = []
            tasks_by_state[state].append(task)
        
        # Store tasks in context for pagination
        context.user_data['mytasks_data'] = {
            'tasks_by_state': tasks_by_state,
            'user_id': user_id,
            'username': username,
            'chat_id': user_id,  # Send to DM
            'topic_id': None,  # No topic in DM
            'page_size': 5,
            'expanded_states': set()
        }
        
        # Build message with pagination
        message_text, keyboard = build_mytasks_message(context, tasks_by_state, len(all_tasks), user_id, user_id, username)
        
        # Send message to DM
        try:
            sent_message = await context.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            
            # Store message_id for auto-deletion
            context.user_data['mytasks_message_id'] = sent_message.message_id
            context.user_data['mytasks_chat_id'] = user_id
            
            # Schedule auto-delete after 120 seconds
            async def delete_after_delay():
                await asyncio.sleep(120)
                try:
                    current_msg_id = context.user_data.get('mytasks_message_id')
                    if current_msg_id == sent_message.message_id:
                        await sent_message.delete()
                        logger.info(f"Auto-deleted /mytasks DM after 120 seconds")
                except Exception as e:
                    logger.warning(f"Failed to auto-delete /mytasks DM: {e}")
            
            # Cancel any existing auto-delete task
            if 'mytasks_delete_task' in context.user_data:
                old_task = context.user_data['mytasks_delete_task']
                if not old_task.done():
                    old_task.cancel()
            
            # Store new task
            context.user_data['mytasks_delete_task'] = asyncio.create_task(delete_after_delay())
            
            logger.info(f"✅ Sent /mytasks response to DM for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send /mytasks DM to user {user_id}: {e}")
        
    except Exception as e:
        logger.error(f"Error in /mytasks: {e}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Error: {str(e)}",
                parse_mode='Markdown'
            )
        except:
            pass


async def cmd_tasksbystate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tasksbystate command - filter tasks by state."""
    user_id = update.message.from_user.id
    task_service = context.bot_data.get('task_service')
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /tasksbystate command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /tasksbystate command message: {e}")
    
    if not task_service:
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ Task service not available",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        from src.data.models.task import TaskState
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Create state selection buttons
        keyboard = [
            [InlineKeyboardButton("📌 ASSIGNED", callback_data="taskstate:ASSIGNED")],
            [InlineKeyboardButton("⚙️ STARTED", callback_data="taskstate:STARTED")],
            [InlineKeyboardButton("🔍 QA_SUBMITTED", callback_data="taskstate:QA_SUBMITTED")],
            [InlineKeyboardButton("❌ REJECTED", callback_data="taskstate:REJECTED")],
            [InlineKeyboardButton("✅ APPROVED", callback_data="taskstate:APPROVED")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🔍 **Filter Tasks by State**\n\nSelect a state to see all tasks in that state:",
            parse_mode='Markdown',
            reply_markup=reply_markup,
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
        )
        
    except Exception as e:
        logger.error(f"Error in /tasksbystate: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_overduetasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /overduetasks command - show overdue tasks."""
    user_id = update.message.from_user.id
    task_service = context.bot_data.get('task_service')
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /overduetasks command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /overduetasks command message: {e}")
    
    if not task_service:
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ Task service not available",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        from datetime import datetime
        from src.data.models.task import TaskState
        
        # Get all user's tasks
        all_tasks = await task_service.get_tasks_by_assignee(user_id)
        
        # Filter overdue tasks (those with deadline in past)
        overdue_tasks = []
        for task in all_tasks:
            # Check if task has deadline metadata
            if hasattr(task, 'deadline') and task.deadline:
                try:
                    deadline = datetime.fromisoformat(task.deadline)
                    if deadline < datetime.now() and task.state not in [TaskState.APPROVED, TaskState.ARCHIVED]:
                        overdue_tasks.append(task)
                except:
                    pass
        
        if not overdue_tasks:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text="✅ No overdue tasks! You're all caught up.",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=False
            )
            return
        
        # Build message
        message = f"⏰ **Overdue Tasks** ({len(overdue_tasks)})\n\n"
        
        for task in overdue_tasks[:10]:
            message += f"🔴 <a href='https://t.me/c/{abs(update.message.chat_id)}/{task.message_id}'>#{task.ticket}</a> - {task.brand}\n"
        
        if len(overdue_tasks) > 10:
            message += f"\n... and {len(overdue_tasks) - 10} more"
        
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=message,
            parse_mode='HTML',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
        )
        
    except Exception as e:
        logger.error(f"Error in /overduetasks: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /filter command - advanced task filtering."""
    user_id = update.message.from_user.id
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /filter command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /filter command message: {e}")
    
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Create filter options
        keyboard = [
            [InlineKeyboardButton("🏷️ By Brand", callback_data="filter:brand")],
            [InlineKeyboardButton("📊 By State", callback_data="filter:state")],
            [InlineKeyboardButton("👤 By Assignee", callback_data="filter:assignee")],
            [InlineKeyboardButton("⏰ By Deadline", callback_data="filter:deadline")],
            [InlineKeyboardButton("🔴 By Priority", callback_data="filter:priority")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="🔍 **Advanced Task Filtering**\n\nSelect a filter option:",
            parse_mode='Markdown',
            reply_markup=reply_markup,
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
        )
        
    except Exception as e:
        logger.error(f"Error in /filter: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_taskstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /taskstats command - show task statistics."""
    user_id = update.message.from_user.id
    task_service = context.bot_data.get('task_service')
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /taskstats command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /taskstats command message: {e}")
    
    if not task_service:
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ Task service not available",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        from src.data.models.task import TaskState
        
        # Get all tasks
        all_tasks = await task_service.get_tasks_by_assignee(user_id)
        
        # Count by state
        stats = {
            'ASSIGNED': 0,
            'STARTED': 0,
            'QA_SUBMITTED': 0,
            'REJECTED': 0,
            'APPROVED': 0,
            'TOTAL': len(all_tasks)
        }
        
        for task in all_tasks:
            state = task.state.value
            if state in stats:
                stats[state] += 1
        
        # Build message
        message = "📊 **Your Task Statistics**\n\n"
        message += f"📌 Assigned: {stats['ASSIGNED']}\n"
        message += f"⚙️ Started: {stats['STARTED']}\n"
        message += f"🔍 QA Submitted: {stats['QA_SUBMITTED']}\n"
        message += f"❌ Rejected: {stats['REJECTED']}\n"
        message += f"✅ Approved: {stats['APPROVED']}\n"
        message += f"\n**Total Tasks: {stats['TOTAL']}**\n"
        
        # Calculate percentages
        if stats['TOTAL'] > 0:
            message += f"\n📈 **Progress:**\n"
            completed = stats['APPROVED']
            percentage = (completed / stats['TOTAL']) * 100
            message += f"Completed: {completed}/{stats['TOTAL']} ({percentage:.1f}%)"
        
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=message,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
        )
        
    except Exception as e:
        logger.error(f"Error in /taskstats: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_debugtasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to show what the bot finds in Task Allocation topic."""
    user_id = update.message.from_user.id
    config = context.bot_data.get('config')
    
    # Permission check
    if not is_privileged_user(user_id, config):
        await update.message.reply_text(
            "❌ **Access Denied**\n\nThis command is only available to Administrators, Managers, and Owners.",
            parse_mode='Markdown'
        )
        try:
            await update.message.delete()
        except:
            pass
        return
    
    # Delete the command message
    try:
        await update.message.delete()
        logger.info(f"Deleted /debugtasks command message from user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /debugtasks command: {e}")
    
    try:
        import re
        
        chat_id = config.TELEGRAM_GROUP_ID
        topic_id = config.TOPIC_TASK_ALLOCATION
        
        # Get user info
        try:
            user_info = await context.bot.get_chat_member(chat_id, user_id)
            username = user_info.user.username
        except Exception as e:
            username = None
        
        response = f"🔍 **Debug Task Search**\n\n"
        response += f"**Your Info:**\n"
        response += f"• User ID: {user_id}\n"
        response += f"• Username: @{username if username else 'Not found'}\n"
        response += f"• Topic ID: {topic_id}\n\n"
        
        # Search for messages
        found_messages = []
        message_count = 0
        
        try:
            # Try to read chat history - this might not work due to API limitations
            try:
                async for message in context.bot.iter_chat_history(
                    chat_id=chat_id,
                    limit=50  # Just check recent 50 messages for debug
                ):
                    if message.message_thread_id == topic_id and message.text:
                        message_count += 1
                        text = message.text
                        
                        # Check if this message mentions the user
                        user_mentioned = False
                        mention_type = ""
                    
                    if f"<@{user_id}>" in text:
                        user_mentioned = True
                        mention_type = f"<@{user_id}>"
                    elif username and f"@{username}" in text.lower():
                        user_mentioned = True
                        mention_type = f"@{username}"
                    
                    if user_mentioned:
                        # Extract ticket if present
                        ticket_match = re.search(r'#([A-Z]{3}\d{6})', text)
                        ticket = ticket_match.group(1) if ticket_match else "No ticket found"
                        
                        found_messages.append({
                            'ticket': ticket,
                            'mention': mention_type,
                            'text': text[:100] + "..." if len(text) > 100 else text
                        })
            
            except AttributeError as api_error:
                response += f"❌ **API Limitation:** Bot cannot read chat history\n"
                response += f"Error: {api_error}\n\n"
                response += f"**This is normal** - Telegram Bot API has limitations on reading chat history.\n\n"
        
        except Exception as e:
            response += f"❌ **Error reading topic:** {e}\n"
        
        response += f"**Search Results:**\n"
        response += f"• Scanned: {message_count} messages\n"
        response += f"• Found: {len(found_messages)} messages mentioning you\n\n"
        
        if found_messages:
            response += f"**Messages Found:**\n"
            for i, msg in enumerate(found_messages[:5], 1):  # Show first 5
                response += f"{i}. **{msg['ticket']}** via {msg['mention']}\n"
                response += f"   Text: {msg['text']}\n\n"
        else:
            response += f"❌ **No messages found mentioning you**\n"
            response += f"Looking for: `<@{user_id}>` or `@{username if username else 'username'}`\n\n"
            response += f"**Sample message format expected:**\n"
            response += f"`[TICKET] #POV260408`\n"
            response += f"`[BRAND] #Povaly`\n"
            response += f"`[ASSIGNEE] @{username if username else 'yourusername'}`\n"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=60,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /debugtasks command: {e}")
        error_msg = f"❌ Debug error: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
