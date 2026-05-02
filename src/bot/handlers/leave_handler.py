"""Leave request handlers for bot commands."""

import logging
import asyncio
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.data.models.leave_request import LeaveStatus
from src.utils.message_utils import send_auto_delete_dm

logger = logging.getLogger(__name__)


async def send_auto_delete_message(context, chat_id, text, parse_mode='Markdown',
                                   message_thread_id=None, delete_after_seconds=20, warning_text=True):
    """Send a message that auto-deletes after specified seconds."""
    if warning_text:
        warning = f"\n\n_⏱️ This message will be deleted in {delete_after_seconds} seconds..._"
        text = text + warning
    
    sent_message = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        message_thread_id=message_thread_id
    )
    
    async def delete_message_later():
        await asyncio.sleep(delete_after_seconds)
        try:
            await sent_message.delete()
        except Exception as e:
            logger.warning(f"Failed to auto-delete message: {e}")
    
    asyncio.create_task(delete_message_later())
    return sent_message


async def cmd_requestleave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /requestleave command - request leave from work."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    config = context.bot_data.get('config')
    leave_service = context.bot_data.get('leave_request_service')
    user_repo = context.bot_data.get('user_repository')
    
    if not leave_service:
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ **Service Not Available**\n\nLeave request service not initialized.",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    # Parse command: /requestleave <start_date> <end_date> <reason> [@replacement]
    if not context.args or len(context.args) < 3:
        help_msg = """📋 **Request Leave**

**Usage:** `/requestleave YYYY-MM-DD YYYY-MM-DD Reason [@replacement]`

**Examples:**
• `/requestleave 2026-05-10 2026-05-15 Family vacation`
• `/requestleave 2026-05-10 2026-05-15 Medical appointment @john`

**Notes:**
• Dates must be in YYYY-MM-DD format
• Reason is required
• Replacement user is optional (specify who handles your tasks)
• Leave will be pending admin approval"""
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=help_msg,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=30,
            warning_text=True
        )
        return
    
    try:
        start_date_str = context.args[0]
        end_date_str = context.args[1]
        reason = " ".join(context.args[2:])
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text="❌ **Invalid Date Format**\n\nDates must be in YYYY-MM-DD format (e.g., 2026-05-10)",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Check for replacement user
        replacement_user_id = None
        if reason.endswith(")"):
            # Check if last word is @username
            parts = reason.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].startswith("@"):
                replacement_username = parts[1].lstrip("@").lower()
                replacement_user = await user_repo.get_user_by_username(replacement_username)
                if replacement_user:
                    replacement_user_id = replacement_user.user_id
                    reason = parts[0]  # Remove username from reason
        
        # Create leave request
        success, message, leave_request = await leave_service.create_leave_request(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            message_id=update.message.message_id,
            replacement_user_id=replacement_user_id
        )
        
        if not success:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text=f"❌ **Error**\n\n{message}",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=15,
                warning_text=True
            )
            return
        
        # Post leave request to Attendance & Leave topic
        duration = (end_date - start_date).days + 1
        replacement_info = ""
        if replacement_user_id:
            replacement_user = await user_repo.get_user(replacement_user_id)
            replacement_info = f"\n**Replacement:** @{replacement_user.username if replacement_user else 'Unknown'}"
        
        leave_msg = f"""📋 **Leave Request**

**Employee:** @{username}
**User ID:** {user_id}
**Dates:** {start_date} to {end_date}
**Duration:** {duration} days
**Reason:** {reason}{replacement_info}
**Status:** ⏳ PENDING

React with:
👍 to approve
👎 to reject"""
        
        try:
            posted_msg = await context.bot.send_message(
                chat_id=config.TELEGRAM_GROUP_ID,
                text=leave_msg,
                parse_mode='Markdown',
                message_thread_id=config.TOPIC_ATTENDANCE_LEAVE
            )
            
            # Update message_id in database
            await context.bot_data.get('db_adapter').conn.execute(
                "UPDATE leave_requests SET message_id = ? WHERE user_id = ? AND start_date = ? AND end_date = ?",
                (posted_msg.message_id, user_id, start_date.isoformat(), end_date.isoformat())
            )
            await context.bot_data.get('db_adapter').conn.commit()
            
        except Exception as e:
            logger.warning(f"Failed to post leave request to topic: {e}")
        
        # Send confirmation DM
        await send_auto_delete_dm(
            context=context,
            user_id=user_id,
            text=f"""✅ **Leave Request Submitted**

**Dates:** {start_date} to {end_date}
**Duration:** {duration} days
**Reason:** {reason}
**Status:** ⏳ Pending approval

Your leave request has been posted to the Attendance & Leave topic for admin review.""",
            delete_after_seconds=120
        )
        
        logger.info(f"✅ Created leave request for user {user_id} from {start_date} to {end_date}")
        
    except Exception as e:
        logger.error(f"Error in /requestleave command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ **Error**\n\n{str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_myleave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myleave command - show user's leave requests."""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    attendance_repo = context.bot_data.get('attendance_repository')
    
    # Delete command message
    try:
        await update.message.delete()
    except:
        pass
    
    if not attendance_repo:
        await send_auto_delete_message(
            context=context,
            chat_id=user_id,
            text="❌ **Service Not Available**",
            parse_mode='Markdown',
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        # Get user's leave requests
        leave_requests = await attendance_repo.get_leave_requests_by_user(user_id)
        
        if not leave_requests:
            await send_auto_delete_message(
                context=context,
                chat_id=user_id,
                text="📭 **No Leave Requests**\n\nYou have not submitted any leave requests.",
                parse_mode='Markdown',
                delete_after_seconds=60,
                warning_text=True
            )
            return
        
        # Build response
        response = f"📋 **Your Leave Requests**\n\n👤 @{username}\n\n"
        
        for req in leave_requests:
            duration = (req.end_date - req.start_date).days + 1
            status_emoji = {
                LeaveStatus.PENDING: "⏳",
                LeaveStatus.APPROVED: "✅",
                LeaveStatus.REJECTED: "❌"
            }.get(req.status, "❓")
            
            response += f"{status_emoji} **{req.status.value}**\n"
            response += f"📅 {req.start_date} to {req.end_date} ({duration} days)\n"
            response += f"📝 {req.reason}\n"
            
            if req.reviewed_at:
                response += f"⏰ Reviewed: {req.reviewed_at.strftime('%Y-%m-%d %H:%M')}\n"
            
            response += "\n"
        
        await send_auto_delete_message(
            context=context,
            chat_id=user_id,
            text=response,
            parse_mode='Markdown',
            delete_after_seconds=120,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /myleave command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=user_id,
            text=f"❌ **Error**\n\n{str(e)}",
            parse_mode='Markdown',
            delete_after_seconds=15,
            warning_text=True
        )


async def cmd_pendingleave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pendingleave command - show pending leave requests (admin only)."""
    user_id = update.message.from_user.id
    config = context.bot_data.get('config')
    attendance_repo = context.bot_data.get('attendance_repository')
    user_repo = context.bot_data.get('user_repository')
    
    # Permission check
    is_privileged = (
        user_id in config.ADMINISTRATORS or
        user_id in config.MANAGERS or
        user_id in config.OWNERS
    )
    
    if not is_privileged:
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ **Access Denied**\n\nOnly Administrators, Managers, and Owners can view pending leave requests.",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    # Delete command message
    try:
        await update.message.delete()
    except:
        pass
    
    if not attendance_repo:
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text="❌ **Service Not Available**",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
        return
    
    try:
        # Get pending leave requests
        pending_requests = await attendance_repo.get_pending_leave_requests()
        
        if not pending_requests:
            await send_auto_delete_message(
                context=context,
                chat_id=update.message.chat_id,
                text="📭 **No Pending Requests**\n\nAll leave requests have been reviewed.",
                parse_mode='Markdown',
                message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
                delete_after_seconds=60,
                warning_text=True
            )
            return
        
        # Build response
        response = f"📋 **Pending Leave Requests** ({len(pending_requests)})\n\n"
        
        for req in pending_requests:
            employee = await user_repo.get_user(req.user_id)
            duration = (req.end_date - req.start_date).days + 1
            
            response += f"👤 @{employee.username if employee else 'Unknown'} (ID: {req.user_id})\n"
            response += f"📅 {req.start_date} to {req.end_date} ({duration} days)\n"
            response += f"📝 {req.reason}\n"
            response += f"⏰ Requested: {req.requested_at.strftime('%Y-%m-%d %H:%M')}\n"
            response += f"🔗 Message ID: {req.message_id}\n\n"
        
        response += "_React with 👍 to approve or 👎 to reject on the leave request messages in Attendance & Leave topic_"
        
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=response,
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=120,
            warning_text=True
        )
        
    except Exception as e:
        logger.error(f"Error in /pendingleave command: {e}", exc_info=True)
        await send_auto_delete_message(
            context=context,
            chat_id=update.message.chat_id,
            text=f"❌ **Error**\n\n{str(e)}",
            parse_mode='Markdown',
            message_thread_id=update.message.message_thread_id if update.message.is_topic_message else None,
            delete_after_seconds=15,
            warning_text=True
        )
