"""Message handler."""

import logging
import re
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from src.config import Config
from src.core.parser.message_parser import MessageParser
from src.data.models.task import TaskState

logger = logging.getLogger(__name__)
parser = MessageParser()


async def move_to_trash(context, message, reason="Deleted message", deleted_by=None, skip_db_sync=False):
    """
    Move a message to trash topic instead of deleting it.
    Also syncs database if it's a task message being deleted.
    
    Args:
        context: Telegram context
        message: Message object to move to trash
        reason: Reason for deletion
        deleted_by: User who deleted the message (optional)
        skip_db_sync: If True, skip database sync (used when updating messages)
    """
    try:
        config = context.bot_data.get('config')
        if not config or not config.TOPIC_TRASH:
            # Fallback to regular deletion if trash topic not configured
            await message.delete()
            return
        
        # Sync database if this is a task message being deleted (unless skip_db_sync is True)
        task_service = context.bot_data.get('task_service')
        if not skip_db_sync and task_service and message.text and message.message_thread_id == config.TOPIC_TASK_ALLOCATION:
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


async def update_user_message_with_new_ticket(context, update, original_text, old_ticket, new_ticket):
    """
    Update the user's original message with the new ticket ID.
    Keeps trying with new tickets if duplicates occur during the process.
    Only shows error if all methods fail completely.
    Adds [CREATOR] field when bot edits/reposts the message.
    Updates message_id in database if message is replaced.
    
    Args:
        context: Telegram context
        update: Telegram update object
        original_text: Original message text
        old_ticket: Old ticket ID (could be empty)
        new_ticket: New generated ticket ID
    """
    try:
        logger.info(f"Silently updating message: '{old_ticket}' -> '{new_ticket}'")
        
        updated_text = original_text
        
        # Get user mention for creator field
        user = update.message.from_user
        user_mention = f"@{user.username}" if user.username else f"@{user.first_name}"
        
        if old_ticket and old_ticket.strip():
            # Replace existing ticket - try multiple formats
            patterns_to_replace = [
                f"[TICKET] #{old_ticket}",
                f"[TICKET] {old_ticket}",
                f"[TICKET]#{old_ticket}",
                f"[TICKET]{old_ticket}",
                f"[TICKET] ##{old_ticket}",
                f"#{old_ticket}",
                old_ticket
            ]
            
            for pattern in patterns_to_replace:
                if pattern in updated_text:
                    updated_text = updated_text.replace(pattern, f"[TICKET] #{new_ticket}")
                    break
        else:
            # Add ticket to empty field
            empty_patterns = [
                "[TICKET]",
                "[TICKET] ",
                "[TICKET]  ",
                "[TICKET]\t"
            ]
            
            for pattern in empty_patterns:
                if pattern in updated_text:
                    updated_text = updated_text.replace(pattern, f"[TICKET] #{new_ticket}", 1)
                    break
        
        # Add [CREATOR] field at the end if not already present
        if "[CREATOR]" not in updated_text:
            # Add line break before [CREATOR] to separate it from other fields
            if not updated_text.endswith('\n'):
                updated_text += '\n'
            updated_text += f"[CREATOR] {user_mention}"
        
        # Only proceed if text actually changed
        if updated_text != original_text:
            try:
                # Method 1: Try to edit the original message
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=update.message.message_id,
                    text=updated_text
                )
                logger.info(f"Successfully updated message via edit with creator field")
                return
                
            except Exception as edit_error:
                logger.info(f"Edit failed, trying delete+repost: {edit_error}")
                
                try:
                    # Method 2: Delete old message and send new one
                    # Skip database sync because we're just updating the message, not deleting the task
                    await move_to_trash(
                        context, 
                        update.message, 
                        f"Message replaced due to ticket update: {old_ticket} -> {new_ticket}",
                        "System",
                        skip_db_sync=True  # Don't delete the task from database!
                    )
                    
                    # Send new corrected message
                    new_message = await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=updated_text,
                        message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
                    )
                    
                    logger.info(f"Successfully replaced message via delete+send with creator field")
                    logger.info(f"🔄 Message replaced: old_id={update.message.message_id}, new_id={new_message.message_id}, ticket={new_ticket}")
                    
                    # CRITICAL: Update the message_id in the database
                    db_adapter = context.bot_data.get('db_adapter')
                    if db_adapter:
                        try:
                            await db_adapter.update_task_message_id(new_ticket, new_message.message_id)
                            logger.info(f"✅ Updated message_id in database: {update.message.message_id} -> {new_message.message_id} for ticket {new_ticket}")
                        except Exception as db_error:
                            logger.error(f"❌ Failed to update message_id in database: {db_error}", exc_info=True)
                    else:
                        logger.error(f"❌ db_adapter not found in context, cannot update message_id for ticket {new_ticket}")
                    
                    return
                    
                except Exception as replace_error:
                    logger.error(f"All message update methods failed: edit={edit_error}, replace={replace_error}")
                    
                    # Only show error if ALL methods fail - and delete it immediately
                    try:
                        error_msg = f"⚠️ Could not update ticket in message. Task created with ticket #{new_ticket}"
                        error_message = await context.bot.send_message(
                            chat_id=update.message.chat_id,
                            text=error_msg,
                            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
                        )
                        
                        # Delete error message immediately (after 3 seconds)
                        await asyncio.sleep(3)
                        await error_message.delete()
                        
                    except Exception as error_msg_error:
                        logger.error(f"Could not even send error message: {error_msg_error}")
        
    except Exception as e:
        logger.error(f"Critical error in message update: {e}")
        # Silent failure - task was still created


async def send_auto_delete_message(context, chat_id, text, parse_mode='Markdown', 
                                   message_thread_id=None, delete_after_seconds=20, warning_text=True):
    """
    Send a message that auto-deletes after specified seconds.
    
    Args:
        context: Telegram context
        chat_id: Chat ID to send message to
        text: Message text
        parse_mode: Parse mode (Markdown, HTML, etc.)
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
        message_thread_id=message_thread_id
    )
    
    # Schedule deletion as a background task (non-blocking)
    async def delete_message_later():
        await asyncio.sleep(delete_after_seconds)
        try:
            await sent_message.delete()
            logger.info(f"Auto-deleted message {sent_message.message_id} after {delete_after_seconds} seconds")
        except Exception as e:
            logger.warning(f"Failed to auto-delete message: {e}")
    
    # Create background task for deletion
    asyncio.create_task(delete_message_later())
    
    return sent_message


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    if not update.message or not update.message.text:
        return
    
    message = update.message
    text = message.text
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    message_id = message.message_id
    topic_id = message.message_thread_id if message.is_topic_message else 0
    
    logger.info(
        f"Received message from user {user_id} (@{username}) in topic {topic_id}: {text[:50]}"
    )
    
    # Get services from bot_data
    config = context.bot_data.get("config")
    task_service = context.bot_data.get("task_service")
    qa_service = context.bot_data.get("qa_service")
    issue_service = context.bot_data.get("issue_service")
    user_repo = context.bot_data.get("user_repository")
    
    if not all([config, task_service, qa_service]):
        logger.error("Services not initialized in bot_data")
        return
    
    # Sync user info - create or update user record with actual Telegram username
    if user_repo:
        try:
            existing_user = await user_repo.get_user(user_id)
            if existing_user:
                # Update username if it changed
                if existing_user.username != username:
                    existing_user.username = username
                    # Get full name safely
                    full_name = getattr(message.from_user, 'full_name', None) or \
                               getattr(message.from_user, 'first_name', None) or \
                               username
                    existing_user.full_name = full_name
                    existing_user.last_active = datetime.now()
                    await user_repo.update_user(existing_user)
                    logger.info(f"✅ Updated user info: {user_id} -> @{username}")
                else:
                    # Just update last active
                    await user_repo.update_last_active(user_id, datetime.now())
            else:
                # Create new user with actual Telegram info
                from src.data.models import User, UserRole
                # Get full name safely
                full_name = getattr(message.from_user, 'full_name', None) or \
                           getattr(message.from_user, 'first_name', None) or \
                           username
                new_user = User(
                    user_id=user_id,
                    username=username,
                    full_name=full_name,
                    role=UserRole.REGULAR,
                    created_at=datetime.now(),
                    last_active=datetime.now()
                )
                await user_repo.create_user(new_user)
                logger.info(f"✅ Created user record: {user_id} -> @{username} ({full_name})")
        except Exception as e:
            logger.error(f"❌ Error syncing user info for {user_id} (@{username}): {e}", exc_info=True)
    
    # ============================================
    # TOPIC PROTECTION: Prevent unauthorized access to restricted topics
    # ============================================
    
    # Define who has admin-level access (can post anywhere)
    admin_users = config.ADMINISTRATORS + config.MANAGERS + config.OWNERS
    is_admin = user_id in admin_users
    
    restricted_topics = {
        config.TOPIC_OFFICIAL_DIRECTIVES: {
            'name': 'Official Directives',
            'allowed': admin_users,  # Admins, Managers, Owners
            'reason': 'Only Administrators, Managers, and Owners can post official directives.'
        },
        config.TOPIC_CENTRAL_ARCHIVE: {
            'name': 'Central Archive',
            'allowed': admin_users,  # Admins/Managers/Owners can post
            'reason': 'This is an archive topic. Only authorized personnel can post here.'
        },
        config.TOPIC_DAILY_SYNC: {
            'name': 'Daily Sync',
            'allowed': admin_users,  # Admins/Managers/Owners can post
            'reason': 'This is a reports topic. Only authorized personnel can post here.'
        },
        config.TOPIC_ADMIN_CONTROL_PANEL: {
            'name': 'Admin Control Panel',
            'allowed': admin_users,  # Admins/Managers/Owners can post
            'reason': 'Only Administrators, Managers, and Owners can access the Admin Control Panel.'
        },
        config.TOPIC_TRASH: {
            'name': 'Trash',
            'allowed': admin_users,  # Admins/Managers/Owners can post
            'reason': 'This is a trash topic. Only authorized personnel can post here.'
        },
    }
    
    # Check if this topic is restricted
    if topic_id in restricted_topics:
        topic_info = restricted_topics[topic_id]
        
        # Check if user is authorized
        is_authorized = user_id in topic_info['allowed']
        
        if not is_authorized:
            # Delete the unauthorized message
            try:
                await message.delete()
                logger.info(f"🚫 Deleted unauthorized message from user {user_id} in restricted topic {topic_id} ({topic_info['name']})")
            except Exception as e:
                logger.error(f"Failed to delete unauthorized message: {e}")
            
            # Send warning DM
            try:
                # Build link to the topic
                group_id_str = str(config.TELEGRAM_GROUP_ID)
                if group_id_str.startswith('-100'):
                    group_id_clean = group_id_str[4:]
                else:
                    group_id_clean = group_id_str
                
                topic_link = f"https://t.me/c/{group_id_clean}/{topic_id}"
                
                from src.utils.message_utils import send_auto_delete_dm
                await send_auto_delete_dm(
                    context=context,
                    user_id=user_id,
                    text=f"""🚫 **Access Denied**

You attempted to post a message in **{topic_info['name']}** topic.

**Reason:** {topic_info['reason']}

[📎 View Topic]({topic_link})

Your message has been automatically deleted.

**Important:** Do not attempt to delete messages in this topic. All activity is monitored and logged.

If you believe you should have access to this topic, please contact an administrator.""",
                    delete_after_seconds=60
                )
                logger.info(f"✉️ Sent topic restriction warning to user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to send topic restriction warning: {e}")
            
            # Stop processing this message
            return
    
    # Check for [PINNED] marker - handle before any other processing
    if text.strip().startswith('[PINNED]'):
        await handle_pinned_message(update, context, config)
        return
    
    # Route based on topic
    if topic_id == config.TOPIC_TASK_ALLOCATION:
        await handle_task_allocation(update, text, user_id, username, message_id, task_service, config, context)
    elif topic_id == config.TOPIC_QA_REVIEW:
        await handle_qa_review(update, text, user_id, username, message_id, qa_service, config, context)
    elif topic_id == config.TOPIC_CORE_OPERATIONS:
        await handle_core_operations(update, text, user_id, username, message_id, issue_service, config, context)
    else:
        logger.debug(f"Message in topic {topic_id} - no specific handler")


async def handle_pinned_message(update: Update, context: ContextTypes.DEFAULT_TYPE, config):
    """Handle messages starting with [PINNED]."""
    message = update.message
    text = message.text
    user_id = message.from_user.id
    
    # Check if user is authorized to pin
    is_authorized = (
        user_id in config.ADMINISTRATORS or 
        user_id in config.MANAGERS or 
        user_id in config.OWNERS
    )
    
    if not is_authorized:
        error_msg = "❌ **Access Denied**\n\nOnly Administrators, Managers, and Owners can pin messages."
        await send_auto_delete_message(
            context=context,
            chat_id=message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=message.message_thread_id if message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        # Delete the [PINNED] message
        try:
            await message.delete()
        except:
            pass
        return
    
    # Remove [PINNED] marker and get the content
    content = text.replace('[PINNED]', '', 1).strip()
    
    # Determine what to do based on content
    if not content:
        # Case 1: Just [PINNED] - use default guide for this topic
        topic_id = message.message_thread_id if message.is_topic_message else None
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
                file_content = f.read()
            
            # Delete the [PINNED] message
            await message.delete()
            
            # Send file content as HTML (keep newlines as-is)
            html_content = file_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            sent_message = await context.bot.send_message(
                chat_id=message.chat_id,
                text=html_content,
                parse_mode='HTML',
                message_thread_id=message.message_thread_id if message.is_topic_message else None
            )
            
            # Pin it
            await context.bot.pin_chat_message(
                chat_id=message.chat_id,
                message_id=sent_message.message_id,
                disable_notification=False
            )
            logger.info(f"Pinned default guide from {default_file}")
            
        except FileNotFoundError:
            await message.reply_text(f"❌ Guide file not found: {default_file}", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error pinning default guide: {e}")
            await message.reply_text(f"❌ Error: {str(e)}", parse_mode='Markdown')
    
    elif content.startswith('docs/') or (content.endswith('.txt') and '/' in content):
        # Case 2: [PINNED] docs/filename.txt - read from file
        try:
            with open(content, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Delete the [PINNED] message
            await message.delete()
            
            # Send file content as HTML (keep newlines as-is)
            html_content = file_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            sent_message = await context.bot.send_message(
                chat_id=message.chat_id,
                text=html_content,
                parse_mode='HTML',
                message_thread_id=message.message_thread_id if message.is_topic_message else None
            )
            
            # Pin it
            await context.bot.pin_chat_message(
                chat_id=message.chat_id,
                message_id=sent_message.message_id,
                disable_notification=False
            )
            logger.info(f"Pinned content from file: {content}")
            
        except FileNotFoundError:
            await message.reply_text(f"❌ File not found: {content}", parse_mode='Markdown')
            await message.delete()
        except Exception as e:
            logger.error(f"Error pinning from file: {e}")
            await message.reply_text(f"❌ Error: {str(e)}", parse_mode='Markdown')
            await message.delete()
    
    else:
        # Case 3: [PINNED] Custom message - just pin the user's message as-is
        try:
            # Pin the message directly in the same topic/thread
            await context.bot.pin_chat_message(
                chat_id=message.chat_id,
                message_id=message.message_id,
                disable_notification=False
            )
            logger.info(f"Pinned custom message from user {user_id} in topic {message.message_thread_id}")
            
        except Exception as e:
            logger.error(f"Error pinning custom message: {e}")
            await message.reply_text(f"❌ Error: {str(e)}", parse_mode='Markdown')


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
        
        # Get user ID from the message author (the person who created/owns the task)
        user_id = message.from_user.id
        
        # Track task deletion in reality map
        db_sync_service = context.bot_data.get('db_sync_service')
        if db_sync_service:
            db_sync_service.track_task_deleted(user_id, task_data.ticket)
        
        # Remove from database
        await task_service.task_repo.db.delete_task(task_data.ticket)
        logger.info(f"✅ Synced database: Removed task {task_data.ticket} after message deletion")
        
    except Exception as e:
        logger.error(f"Error syncing database on task deletion: {e}", exc_info=True)


async def handle_task_allocation(update, text, user_id, username, message_id, task_service, config, context):
    """
    Handle task creation in Task Allocation topic.
    
    Workflow:
    1. Validate message format
    2. Parse task data
    3. Generate or validate ticket ID
    4. Create task in database with ASSIGNED state
    5. Track in topic scanner and reality map
    6. Update message with final ticket ID
    
    Error handling:
    - Format violations: Move to trash, send DM with correction
    - Duplicate tickets: Auto-regenerate up to 5 times
    - Creation failures: Send error message, log for debugging
    """
    
    logger.info(f"📝 Processing task allocation from user {user_id} (@{username}), message {message_id}")
    
    # ============================================================================
    # STEP 1: VALIDATE MESSAGE FORMAT
    # ============================================================================
    is_valid, error_msg = parser.validate_format(text, 'task')
    
    if not is_valid:
        logger.warning(f"❌ Format violation: {error_msg}")
        await _handle_format_violation(context, update, user_id, error_msg, config)
        return
    
    logger.info(f"✅ Format validation passed")
    
    # ============================================================================
    # STEP 2: PARSE TASK DATA
    # ============================================================================
    task_data = parser.parse_task_allocation(text)
    if not task_data:
        logger.error(f"❌ Failed to parse valid task message")
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ Failed to parse task data. Please check format and try again.",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )
        return
    
    logger.info(f"✅ Task data parsed: brand={task_data.brand}, assignee={task_data.assignee_username}")
    
    # ============================================================================
    # STEP 3: GENERATE OR VALIDATE TICKET ID
    # ============================================================================
    from src.core.ticket_generator import TicketGenerator
    from src.core.brand_mapper import BrandMapper
    
    db_adapter = context.bot_data.get("db_adapter")
    brand_mapper = BrandMapper()
    ticket_gen = TicketGenerator(db_adapter, brand_mapper)
    
    original_ticket = task_data.ticket
    ticket_was_generated = False
    
    # Check if ticket needs auto-generation
    if not task_data.ticket or task_data.ticket.strip() == '' or ticket_gen.is_auto_ticket_placeholder(task_data.ticket):
        brand_name = task_data.brand if task_data.brand else "Povaly"
        try:
            # Ensure database is committed before generating
            await db_adapter.conn.commit()
            
            generated_ticket = await ticket_gen.generate_ticket_id(brand_name)
            task_data.ticket = generated_ticket
            ticket_was_generated = True
            logger.info(f"🎫 Auto-generated ticket: {generated_ticket}")
        except Exception as e:
            logger.error(f"❌ Ticket generation failed: {e}", exc_info=True)
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ Error generating ticket: {str(e)}",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=20,
                warning_text=True
            )
            return
    
    logger.info(f"✅ Ticket ID ready: {task_data.ticket}")
    
    # ============================================================================
    # STEP 4: CREATE TASK IN DATABASE
    # ============================================================================
    try:
        logger.info(f"📊 Creating task: ticket={task_data.ticket}, brand={task_data.brand}, assignee={task_data.assignee_username}")
        
        # CRITICAL: Look up assignee's user_id from username or handle group mentions
        user_repo = context.bot_data.get("user_repository")
        config = context.bot_data.get("config")
        assignee_ids = []  # List of user IDs to assign task to
        assignee_username = task_data.assignee_username.lower()
        
        # Check for group mentions
        if assignee_username in ['allmember', 'allmembers', 'all']:
            # Get all users from database
            all_users = await user_repo.get_all_users() if user_repo else []
            assignee_ids = [u.user_id for u in all_users]
            logger.info(f"✅ Group mention @allmember: Assigning to {len(assignee_ids)} users")
            
        elif assignee_username in ['employees', 'employee']:
            # Get all users except admins, managers, owners
            all_users = await user_repo.get_all_users() if user_repo else []
            privileged_ids = set()
            if config:
                privileged_ids = set(config.ADMINISTRATORS + config.MANAGERS + config.OWNERS)
            assignee_ids = [u.user_id for u in all_users if u.user_id not in privileged_ids]
            logger.info(f"✅ Group mention @employees: Assigning to {len(assignee_ids)} employees")
            
        elif assignee_username in ['owners', 'owner']:
            assignee_ids = list(config.OWNERS) if config else []
            logger.info(f"✅ Group mention @owners: Assigning to {len(assignee_ids)} owners")
            
        elif assignee_username in ['managers', 'manager']:
            assignee_ids = list(config.MANAGERS) if config else []
            logger.info(f"✅ Group mention @managers: Assigning to {len(assignee_ids)} managers")
            
        elif assignee_username in ['admins', 'admin', 'administrators', 'administrator']:
            assignee_ids = list(config.ADMINISTRATORS) if config else []
            logger.info(f"✅ Group mention @admins: Assigning to {len(assignee_ids)} administrators")
            
        elif assignee_username in ['commanders', 'commander', 'leadership']:
            # All admins, managers, and owners
            if config:
                assignee_ids = list(set(config.ADMINISTRATORS + config.MANAGERS + config.OWNERS))
            logger.info(f"✅ Group mention @commanders: Assigning to {len(assignee_ids)} leaders")
            
        else:
            # Single user lookup
            if user_repo and task_data.assignee_username:
                assignee_user = await user_repo.get_user_by_username(task_data.assignee_username)
                if assignee_user:
                    assignee_ids = [assignee_user.user_id]
                    logger.info(f"✅ Found assignee: @{task_data.assignee_username} -> user_id {assignee_user.user_id}")
                else:
                    logger.warning(f"⚠️ Assignee @{task_data.assignee_username} not found in database")
                    logger.warning(f"⚠️ User must interact with bot first before tasks can be assigned to them")
                    logger.warning(f"⚠️ Assigning task to creator {user_id} instead")
                    assignee_ids = [user_id]
                    
                    # Send notification to creator
                    await send_auto_delete_message(
                        context=context,
                        chat_id=update.message.chat_id,
                        text=f"⚠️ **Assignee Not Found**\n\nUser @{task_data.assignee_username} hasn't interacted with the bot yet.\n\nTask will be assigned to you. Ask @{task_data.assignee_username} to send any message to the bot first.",
                        parse_mode='Markdown',
                        message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                        delete_after_seconds=30,
                        warning_text=True
                    )
        
        # If no assignees found, assign to creator
        if not assignee_ids:
            assignee_ids = [user_id]
            logger.warning(f"⚠️ No assignees found, assigning to creator {user_id}")
        
        # Use the first assignee as primary (for backward compatibility with single-assignee tasks)
        primary_assignee_id = assignee_ids[0]
        
        # CRITICAL FIX: Ensure database is fully committed before checking for duplicates
        await db_adapter.conn.commit()
        logger.info(f"💾 Pre-creation commit to ensure clean state")
        
        task = await task_service.create_task(
            ticket=task_data.ticket,
            brand=task_data.brand,
            assignee_id=primary_assignee_id,  # Use primary assignee
            creator_id=user_id,
            message_id=message_id,
            topic_id=update.message.message_thread_id or 0
        )
        
        if task:
            logger.info(f"✅ Task created successfully: {task_data.ticket} (state: {task.state})")
            
            # If multiple assignees, add them to task_assignees table
            if len(assignee_ids) > 1:
                try:
                    for idx, assignee_id in enumerate(assignee_ids):
                        is_primary = (idx == 0)  # First one is primary
                        await db_adapter.conn.execute("""
                            INSERT INTO task_assignees (ticket, assignee_id, status, assigned_at, is_primary)
                            VALUES (?, ?, ?, ?, ?)
                        """, (task_data.ticket, assignee_id, 'ASSIGNED', datetime.now().isoformat(), 1 if is_primary else 0))
                    await db_adapter.conn.commit()
                    logger.info(f"✅ Added {len(assignee_ids)} assignees to task {task_data.ticket}")
                except Exception as e:
                    logger.error(f"❌ Failed to add multiple assignees: {e}", exc_info=True)
            
            # Ensure database is committed immediately after task creation
            await db_adapter.conn.commit()
            logger.info(f"💾 Database committed after task creation")
            
            # Verify task was actually saved
            verify_task = await task_service.get_task(task_data.ticket)
            if verify_task:
                logger.info(f"✅ Task verified in database: {task_data.ticket}")
            else:
                logger.error(f"❌ Task NOT found in database after creation: {task_data.ticket}")
            
            # ====================================================================
            # STEP 5: TRACK IN TOPIC SCANNER AND REALITY MAP
            # ====================================================================
            await _track_task_creation(context, primary_assignee_id, task_data, message_id, text)
            
            # ====================================================================
            # STEP 6: UPDATE MESSAGE WITH FINAL TICKET ID
            # ====================================================================
            if ticket_was_generated or task_data.ticket != original_ticket:
                await update_user_message_with_new_ticket(
                    context, update, text, original_ticket, task_data.ticket
                )
                logger.info(f"📝 Updated message with ticket: {original_ticket} → {task_data.ticket}")
            
            logger.info(f"✅ Task allocation complete: {task_data.ticket}")
        
        else:
            # Task creation returned None - likely duplicate
            logger.warning(f"⚠️ Task creation returned None for {task_data.ticket}")
            await _handle_duplicate_ticket(
                context, update, task_service, ticket_gen, task_data, user_id, primary_assignee_id, message_id, text
            )
    
    except Exception as e:
        logger.error(f"❌ Unexpected error during task creation: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Error creating task: {str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )


async def _handle_format_violation(context, update, user_id, error_msg, config):
    """Handle format validation failures."""
    logger.info(f"📋 Handling format violation for user {user_id}")
    
    # Move malformed message to trash
    if config.VIOLATION_AUTO_DELETE_MALFORMED:
        try:
            await move_to_trash(
                context, 
                update.message, 
                f"Format violation: {error_msg}", 
                "System"
            )
            logger.info(f"🗑️ Moved malformed message to trash")
        except Exception as e:
            logger.error(f"Failed to move message to trash: {e}")
    
    # Send correction DM to user
    try:
        from src.utils.message_utils import send_permanent_dm
        await send_permanent_dm(
            context=context,
            user_id=user_id,
            text=f"""❌ **Task Format Error**

Your message was deleted due to format violation.

**Problem:** {error_msg}

**Correct format:**
```
[TICKET] (leave blank for auto-generation)
[BRAND] #VorosaBajar (type # to select: #VorosaBajar, #GSMAura, #Povaly)
[TASK] Product page SEO optimization
[ASSIGNEE] @username
[DEADLINE] 28 Apr 2026 | 6:00 PM GMT+6
[RESOURCES] Google Doc Link
```

**Required fields:**
• [TICKET] - Leave blank, bot auto-generates
• [BRAND] - Type # to select brand from list
• [ASSIGNEE] - Username with @

**Optional fields:**
• [TASK] - Task description
• [DEADLINE] - Due date
• [RESOURCES] - Links or files

**Tip:** Use /newtask command for a pre-filled template!

Please repost with correct format."""
        )
        logger.info(f"📧 Sent format correction DM to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send DM: {e}")


async def _track_task_creation(context, user_id, task_data, message_id, text):
    """Track task creation in topic scanner and reality map."""
    try:
        # Track in reality map
        db_sync_service = context.bot_data.get('db_sync_service')
        if db_sync_service:
            db_sync_service.track_task_created(user_id, task_data.ticket)
            logger.info(f"📍 Tracked in reality map: {task_data.ticket}")
        
        # Track in topic scanner cache
        topic_scanner = context.bot_data.get('topic_scanner')
        if topic_scanner:
            from src.services.topic_scanner_service import TopicTask
            topic_task = TopicTask(
                ticket=task_data.ticket,
                assignee_username=task_data.assignee_username,
                assignee_id=user_id,
                brand=task_data.brand,
                message_id=message_id,
                message_date=datetime.now(),
                message_text=text,
                topic_id=0  # Will be set by topic scanner
            )
            
            if user_id not in topic_scanner.topic_tasks:
                topic_scanner.topic_tasks[user_id] = []
            topic_scanner.topic_tasks[user_id].append(topic_task)
            logger.info(f"📍 Tracked in topic scanner: {task_data.ticket}")
    
    except Exception as e:
        logger.error(f"Error tracking task creation: {e}", exc_info=True)


async def _handle_duplicate_ticket(context, update, task_service, ticket_gen, task_data, user_id, assignee_id, message_id, original_text):
    """Handle duplicate ticket by attempting regeneration with manual increment."""
    logger.info(f"🔄 Handling duplicate ticket: {task_data.ticket}")
    
    # Get database adapter
    db_adapter = context.bot_data.get("db_adapter")
    
    # Check if it's actually a duplicate
    existing_task = await task_service.get_task(task_data.ticket)
    if not existing_task:
        logger.error(f"Task creation failed but no existing task found")
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ Failed to create task. Please try again.",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )
        return
    
    logger.info(f"🔄 Duplicate confirmed: {task_data.ticket} (state: {existing_task.state})")
    
    # Extract ticket components for manual increment
    # Format: [BRANDYYMM##] e.g., GSM260401
    original_ticket = task_data.ticket
    brand_code = original_ticket[:3]  # e.g., "GSM"
    yymm = original_ticket[3:7]       # e.g., "2604"
    
    try:
        current_serial = int(original_ticket[7:])  # e.g., 01
    except (ValueError, IndexError):
        logger.error(f"❌ Invalid ticket format: {original_ticket}")
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Invalid ticket format: {original_ticket}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )
        return
    
    # Find the next available ticket number by querying database
    # This is more reliable than trying to create and checking
    logger.info(f"🔍 Finding next available ticket after {original_ticket}")
    
    try:
        # Query database for all tickets with this prefix
        prefix = f"{brand_code}{yymm}"
        query = "SELECT ticket FROM tasks WHERE ticket LIKE ? ORDER BY ticket DESC LIMIT 50"
        
        async with db_adapter.conn.execute(query, (f"{prefix}%",)) as cursor:
            rows = await cursor.fetchall()
            
            # Find the highest serial number
            max_serial = current_serial
            for row in rows:
                ticket = row[0]
                try:
                    serial = int(ticket[7:])
                    if serial > max_serial:
                        max_serial = serial
                except (ValueError, IndexError):
                    continue
            
            # Next available ticket
            next_serial = max_serial + 1
            new_ticket = f"{brand_code}{yymm}{next_serial:02d}"
            
            logger.info(f"✅ Next available ticket: {new_ticket} (highest found: {max_serial})")
            
            # Create task with the new ticket
            task = await task_service.create_task(
                ticket=new_ticket,
                brand=task_data.brand,
                assignee_id=assignee_id,  # Use the same assignee_id from above
                creator_id=user_id,
                message_id=message_id,
                topic_id=update.message.message_thread_id or 0
            )
            
            if task:
                logger.info(f"✅ Task created with regenerated ticket: {new_ticket}")
                
                # Update task_data with the new ticket for tracking
                task_data.ticket = new_ticket
                
                # Track the new task with the CORRECT ticket and assignee
                await _track_task_creation(context, assignee_id, task_data, message_id, original_text)
                
                # Update message with new ticket - pass original text to preserve template
                await update_user_message_with_new_ticket(
                    context, update, original_text, original_ticket, new_ticket
                )
                
                logger.info(f"✅ Duplicate ticket regeneration successful: {original_ticket} → {new_ticket}")
                return
            else:
                logger.error(f"❌ Failed to create task with {new_ticket}")
                raise Exception(f"Task creation failed for {new_ticket}")
        
    except Exception as e:
        logger.error(f"❌ Regeneration failed: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ Failed to create task. Ticket {task_data.ticket} already exists and regeneration failed.\nPlease try again with /newtask command.",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )


async def handle_qa_review(update, text, user_id, username, message_id, qa_service, config, context):
    """Handle messages in QA Review topic."""
    import asyncio
    
    # Validate format
    is_valid, error_msg = parser.validate_format(text, 'qa')
    
    if not is_valid:
        # Format violation detected
        logger.warning(f"QA format violation by user {user_id}: {error_msg}")
        
        # Delete the malformed message
        if config.VIOLATION_AUTO_DELETE_MALFORMED:
            try:
                await context.bot.delete_message(
                    chat_id=update.message.chat_id,
                    message_id=message_id
                )
                logger.info(f"Deleted malformed QA message {message_id}")
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
        
        # Send DM to user (permanent - educational)
        try:
            from src.utils.message_utils import send_permanent_dm
            await send_permanent_dm(
                context=context,
                user_id=user_id,
                text=f"""❌ **QA Submission Format Error**

Your message was deleted due to format violation.

**Problem:** {error_msg}

**Correct format:**
```
[TICKET] #POV260406
[BRAND] #GSMAura
[ASSET] https://gsmaura.com/blog/budget-smartphones-2026
```

**Required fields:**
• [TICKET] - Ticket ID with #
• [BRAND] - Brand name with #
• [ASSET] - Asset URL or description

Please repost with correct format."""
            )
            logger.info(f"Sent QA format error DM to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send DM: {e}")
        
        return
    
    # Parse QA data
    qa_data = parser.parse_qa_submission(text)
    if not qa_data:
        logger.warning(f"Failed to parse valid QA message from user {user_id}")
        return
    
    # Submit for QA
    try:
        submission = await qa_service.submit_for_qa(
            ticket=qa_data.ticket,
            brand=qa_data.brand,
            asset=qa_data.asset,
            submitter_id=user_id,
            message_id=message_id
        )
        
        if submission:
            logger.info(f"QA submission created for {qa_data.ticket}")
            # Silent success - user's message stays as confirmation
        else:
            logger.warning(f"Failed to create QA submission for {qa_data.ticket}")
            error_msg = f"⚠️ Failed to submit for QA. Task {qa_data.ticket} may not exist."
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=20,
                warning_text=True
            )
    except Exception as e:
        logger.error(f"Error submitting QA: {e}")
        error_msg = f"❌ Error submitting QA: {str(e)}"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )


async def handle_core_operations(update, text, user_id, username, message_id, issue_service, config, context):
    """Handle messages in Core Operations topic."""
    import asyncio
    
    logger.info(f"Processing Core Operations message from user {user_id}")
    
    # Check if this looks like an issue message
    if not issue_service.is_issue_message(text):
        logger.debug(f"Message from user {user_id} doesn't look like an issue format")
        return
    
    # Validate format
    is_valid, error_msg = issue_service.validate_issue_format(text)
    
    logger.info(f"Issue validation result: valid={is_valid}, error={error_msg}")
    
    if not is_valid:
        # Format violation detected
        logger.warning(f"Issue format violation by user {user_id}: {error_msg}")
        
        # Delete the malformed message
        if config.VIOLATION_AUTO_DELETE_MALFORMED:
            try:
                await move_to_trash(
                    context, 
                    update.message, 
                    f"Issue format violation: {error_msg}", 
                    "System"
                )
                logger.info(f"Moved malformed issue message to trash: {message_id}")
            except Exception as e:
                logger.error(f"Failed to move malformed message to trash: {e}")
        
        # Send DM to user (permanent - educational)
        try:
            from src.utils.message_utils import send_permanent_dm
            await send_permanent_dm(
                context=context,
                user_id=user_id,
                text=f"""❌ **Issue Format Error**

Your message was deleted due to format violation.

**Problem:** {error_msg}

**Correct format:**
```
[TICKET] #POV260406 (existing task ticket)
[ISSUE] Short descriptive title
[DETAILS] Detailed explanation of the issue
[PRIORITY] LOW / MEDIUM / HIGH / CRITICAL
[ASSIGNEE] @username (optional)
```

**Required fields:**
• [TICKET] - Existing task ticket ID that has the problem (e.g., #POV260406)
• [ISSUE] - Brief title describing the issue
• [DETAILS] - Detailed explanation
• [PRIORITY] - Must be LOW, MEDIUM, HIGH, or CRITICAL

**Optional fields:**
• [ASSIGNEE] - Username with @ (can be left empty)

**Important:** Issues are for reporting problems with existing tasks. Use the ticket ID of the task that has the problem.

**Example:**
```
[TICKET] #POV260415
[ISSUE] Login system not working
[DETAILS] Users cannot log in to the dashboard. Error shows "Invalid credentials" even with correct password. Started happening after yesterday's update.
[PRIORITY] HIGH
[ASSIGNEE] @techsupport
```

Please repost with correct format."""
            )
            logger.info(f"Sent issue format error DM to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send DM: {e}")
        
        return
    
    # Parse issue data
    issue_data = issue_service.parse_issue_message(text)
    if not issue_data:
        logger.warning(f"Failed to parse valid issue message from user {user_id}")
        # Get validation error details
        is_valid, error_msg = issue_service.parser.validate_format(text)
        if not is_valid:
            logger.warning(f"Issue validation failed: {error_msg}")
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Invalid Issue Format**\n\n{error_msg}",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=20,
                warning_text=True
            )
        return
    
    # Create issue
    try:
        issue = await issue_service.create_issue(
            issue_data=issue_data,
            creator_id=user_id,
            message_id=message_id,
            topic_id=update.message.message_thread_id or 0
        )
        
        if issue:
            logger.info(f"Issue {issue.issue_ticket} created successfully for task {issue_data.ticket}")
            
            # If issue ticket was auto-corrected, notify the user
            if issue_data.issue_ticket and issue_data.issue_ticket != issue.issue_ticket:
                # User provided a ticket that was changed (duplicate or invalid)
                username = update.message.from_user.username or update.message.from_user.first_name
                correction_msg = (
                    f"⚠️ **@{username}** - Please Edit Your Issue Ticket\n\n"
                    f"You entered: `{issue_data.issue_ticket}`\n"
                    f"Correct ticket: `{issue.issue_ticket}`\n\n"
                    f"👆 Please edit your message above and change [ISSUETICKET] to:\n"
                    f"`[ISSUETICKET] #{issue.issue_ticket}`\n\n"
                    f"_This message will auto-delete in 15 seconds._\n"
                    f"_If not edited within 5 minutes, you'll receive a DM reminder._"
                )
                
                # Reply to the user's message
                reminder_message = await context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text=correction_msg,
                    parse_mode='Markdown',
                    reply_to_message_id=update.message.message_id,
                    message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None
                )
                
                logger.info(f"Sent correction notice for issue {issue.issue_ticket} (user entered {issue_data.issue_ticket})")
                
                # Schedule auto-delete after 15 seconds
                async def delete_reminder_after_15s():
                    await asyncio.sleep(15)
                    try:
                        await reminder_message.delete()
                        logger.info(f"Auto-deleted correction notice after 15 seconds")
                    except Exception as e:
                        logger.warning(f"Failed to auto-delete correction notice: {e}")
                
                asyncio.create_task(delete_reminder_after_15s())
                
                # Build message link for DM
                chat_id_str = str(update.message.chat_id)
                if chat_id_str.startswith('-100'):
                    group_id = chat_id_str[4:]
                else:
                    group_id = chat_id_str.lstrip('-')
                
                topic_id = update.message.message_thread_id if update.message.is_topic_message else None
                if topic_id:
                    message_link = f"https://t.me/c/{group_id}/{topic_id}/{update.message.message_id}"
                else:
                    message_link = f"https://t.me/c/{group_id}/{update.message.message_id}"
                
                # Schedule a reminder DM after 5 minutes
                async def send_reminder_dm():
                    await asyncio.sleep(300)  # 5 minutes
                    try:
                        dm_text = (
                            f"⏰ **Reminder: Edit Issue Ticket**\n\n"
                            f"You created issue `{issue.issue_ticket}` but your message still shows `{issue_data.issue_ticket}`.\n\n"
                            f"Please edit your message and change [ISSUETICKET] to:\n"
                            f"`[ISSUETICKET] #{issue.issue_ticket}`\n\n"
                            f"[Click here to go to your message]({message_link})\n\n"
                            f"_This keeps the records accurate._"
                        )
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=dm_text,
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                        logger.info(f"Sent DM reminder to user {user_id} about issue {issue.issue_ticket}")
                            
                    except Exception as e:
                        logger.warning(f"Failed to send DM reminder: {e}")
                
                # Create the reminder task
                asyncio.create_task(send_reminder_dm())
                logger.info(f"Scheduled 5-minute DM reminder for user {user_id} about issue {issue.issue_ticket}")
            
            # Log the issue creation for audit
            logger.info(f"Created issue: {issue.issue_ticket} (Task: {issue.ticket}) - {issue.title} (Priority: {issue.priority.value})")
        else:
            # Issue creation failed for unknown reason
            logger.warning(f"Failed to create issue for task {issue_data.ticket}")
            error_msg = f"⚠️ Failed to create issue. Please check the format and try again."
            
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=error_msg,
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=20,
                warning_text=True
            )
    except Exception as e:
        logger.error(f"Error creating issue: {e}", exc_info=True)
        error_msg = f"❌ Error creating issue: {str(e)}\n\n_Check logs for details_"
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=error_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=20,
            warning_text=True
        )


def setup_message_handlers(application: Application, config: Config):
    """Setup message handlers."""
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    logger.info("Message handlers registered")
