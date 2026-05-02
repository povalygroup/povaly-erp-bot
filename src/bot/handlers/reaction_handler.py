"""Reaction handler for tasks and issues with proper state management."""

import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, Application
from src.config import Config
from src.data.models.task import TaskState

logger = logging.getLogger(__name__)


async def send_invalid_reaction_warning(context, user_id, emoji, entity_type, entity_id, reason, message_link=None):
    """
    Send DM to user explaining why their reaction was invalid.
    
    Args:
        context: Bot context
        user_id: User who added the invalid reaction
        emoji: The reaction emoji that was invalid
        entity_type: Type of entity (task, QA submission, etc.)
        entity_id: ID of the entity (ticket number)
        reason: Explanation of why it was invalid
        message_link: Optional link to the message
    """
    try:
        from src.utils.message_utils import send_auto_delete_dm
        
        message_text = f"❌ **Invalid Reaction**\n\nYour {emoji} reaction on {entity_type} **{entity_id}** was not processed.\n\n**Reason:** {reason}"
        
        if message_link:
            message_text += f"\n\n[📎 View Message]({message_link})\n\n**Action Required:** Please remove your {emoji} reaction from the message by clicking it again."
        
        await send_auto_delete_dm(
            context=context,
            user_id=user_id,
            text=message_text,
            delete_after_seconds=30
        )
        logger.info(f"✉️ Sent invalid reaction warning to user {user_id} for {emoji} on {entity_type} {entity_id}")
    except Exception as e:
        logger.warning(f"Failed to send invalid reaction warning to user {user_id}: {e}")


async def handle_reaction_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle reaction updates for both tasks and issues.
    
    Reactions trigger state transitions:
    - Tasks: 👍 (ASSIGNED→STARTED), ❤️ (QA_SUBMITTED→APPROVED), 👎 (QA_SUBMITTED→REJECTED), 🔥 (exemption)
    - Issues: 👍 (claim), ❤️ (resolve), 👎 (reject)
    - Commands list: 👍 (extend time to 10 minutes)
    """
    
    # Check if this is a reaction update
    if not update.message_reaction:
        logger.debug("No message_reaction in update")
        return
    
    reaction_update = update.message_reaction
    message_id = reaction_update.message_id
    chat_id = reaction_update.chat.id
    user_id = reaction_update.user.id
    
    logger.info(f"🔔 Reaction update received: message_id={message_id}, user_id={user_id}, chat_id={chat_id}")
    
    # Get the new and old reactions
    new_reactions = reaction_update.new_reaction
    old_reactions = reaction_update.old_reaction
    
    logger.info(f"  Old reactions: {[r.emoji for r in old_reactions] if old_reactions else []}")
    logger.info(f"  New reactions: {[r.emoji for r in new_reactions] if new_reactions else []}")
    
    # Get services
    config = context.bot_data.get("config")
    task_service = context.bot_data.get("task_service")
    issue_service = context.bot_data.get("issue_service")
    
    if not config or not task_service or not issue_service:
        logger.error("Config or services not initialized")
        return
    
    try:
        # Convert reactions to sets for easier comparison
        old_emoji_set = {r.emoji for r in old_reactions} if old_reactions else set()
        new_emoji_set = {r.emoji for r in new_reactions} if new_reactions else set()
        
        # Find added and removed reactions
        added_reactions = new_emoji_set - old_emoji_set
        removed_reactions = old_emoji_set - new_emoji_set
        
        logger.info(f"Reaction update on message {message_id}: Added={added_reactions}, Removed={removed_reactions}")
        
        # Check if this is a /commands message
        commands_message_id = context.user_data.get('commands_message_id')
        commands_user_id = context.user_data.get('commands_user_id')
        
        if message_id == commands_message_id and user_id == commands_user_id:
            # Handle reaction on /commands message
            if '👍' in added_reactions:
                # User wants to keep the message for 10 minutes
                context.user_data['commands_extended'] = True
                
                # Cancel existing delete task
                if 'commands_delete_task' in context.user_data:
                    old_task = context.user_data['commands_delete_task']
                    if not old_task.done():
                        old_task.cancel()
                        logger.info(f"Cancelled 120s auto-delete for /commands message")
                
                # Schedule new delete after 10 minutes
                async def delete_after_10_minutes():
                    await asyncio.sleep(600)  # 10 minutes
                    try:
                        await context.bot.delete_message(
                            chat_id=context.user_data.get('commands_chat_id'),
                            message_id=message_id
                        )
                        logger.info(f"Auto-deleted /commands message after 10 minutes")
                    except Exception as e:
                        logger.warning(f"Failed to auto-delete /commands message: {e}")
                
                context.user_data['commands_delete_task'] = asyncio.create_task(delete_after_10_minutes())
                logger.info(f"Extended /commands message lifetime to 10 minutes")
                return
        
        # Check if this is a /myissues message
        myissues_message_id = context.user_data.get('myissues_message_id')
        if message_id == myissues_message_id:
            # Handle reaction on /myissues message
            if '👏' in added_reactions:
                # User wants to keep the message for 10 minutes
                context.user_data['myissues_extended'] = True
                
                # Cancel existing delete task
                if 'myissues_delete_task' in context.user_data:
                    old_task = context.user_data['myissues_delete_task']
                    if not old_task.done():
                        old_task.cancel()
                        logger.info(f"Cancelled 40s auto-delete for /myissues message")
                
                # Schedule new delete after 10 minutes
                async def delete_after_10_minutes():
                    await asyncio.sleep(600)  # 10 minutes
                    try:
                        await context.bot.delete_message(
                            chat_id=context.user_data.get('myissues_chat_id'),
                            message_id=message_id
                        )
                        logger.info(f"Auto-deleted /myissues message after 10 minutes")
                    except Exception as e:
                        logger.warning(f"Failed to auto-delete /myissues message: {e}")
                
                context.user_data['myissues_delete_task'] = asyncio.create_task(delete_after_10_minutes())
                logger.info(f"Extended /myissues message lifetime to 10 minutes")
                return
        
        # Check if this is a /myclaimedissues message
        myclaimedissues_message_id = context.user_data.get('myclaimedissues_message_id')
        if message_id == myclaimedissues_message_id:
            # Handle reaction on /myclaimedissues message
            if '👏' in added_reactions:
                # User wants to keep the message for 10 minutes
                context.user_data['myclaimedissues_extended'] = True
                
                # Cancel existing delete task
                if 'myclaimedissues_delete_task' in context.user_data:
                    old_task = context.user_data['myclaimedissues_delete_task']
                    if not old_task.done():
                        old_task.cancel()
                        logger.info(f"Cancelled 40s auto-delete for /myclaimedissues message")
                
                # Schedule new delete after 10 minutes
                async def delete_after_10_minutes():
                    await asyncio.sleep(600)  # 10 minutes
                    try:
                        await context.bot.delete_message(
                            chat_id=context.user_data.get('myclaimedissues_chat_id'),
                            message_id=message_id
                        )
                        logger.info(f"Auto-deleted /myclaimedissues message after 10 minutes")
                    except Exception as e:
                        logger.warning(f"Failed to auto-delete /myclaimedissues message: {e}")
                
                context.user_data['myclaimedissues_delete_task'] = asyncio.create_task(delete_after_10_minutes())
                logger.info(f"Extended /myclaimedissues message lifetime to 10 minutes")
                return
        
        # Try to find task first (Task Allocation topic)
        task = await task_service.get_task_by_message_id(message_id)
        if task:
            logger.info(f"✅ Found task {task.ticket} for message {message_id} (state: {task.state.value}, assignee: {task.assignee_id})")
            await process_task_reactions(
                task, user_id, added_reactions, removed_reactions,
                task_service, context, config
            )
            return
        else:
            logger.info(f"❌ No task found for message {message_id}")
        
        # Try to find issue (Core Operations topic)
        issue = await issue_service.get_issue_by_message_id(message_id)
        if issue:
            logger.info(f"✅ Found issue {issue.ticket} for message {message_id}")
            await process_issue_reactions(
                issue, user_id, added_reactions, removed_reactions,
                issue_service, context, config
            )
            return
        else:
            logger.info(f"❌ No issue found for message {message_id}")
        
        # Try to find QA submission (QA & Review topic)
        qa_service = context.bot_data.get("qa_service")
        if qa_service:
            from src.data.repositories.qa_repository import QARepository
            qa_repo = QARepository(context.bot_data.get('db_adapter'))
            qa_submission = await qa_repo.get_submission_by_message_id(message_id)
            if qa_submission:
                logger.info(f"✅ Found QA submission {qa_submission.ticket} for message {message_id}")
                await process_qa_reactions(
                    qa_submission, user_id, added_reactions, removed_reactions,
                    qa_service, qa_repo, context, config
                )
                return
            else:
                logger.info(f"❌ No QA submission found for message {message_id}")
        
        # Try to find admin alert (Admin Control Panel topic)
        from src.data.repositories.admin_alert_repository import AdminAlertRepository
        db_adapter = context.bot_data.get('db_adapter')
        if db_adapter:
            admin_alert_repo = AdminAlertRepository(db_adapter)
            admin_alert = await admin_alert_repo.get_alert_by_message_id(message_id)
            if admin_alert:
                logger.info(f"✅ Found admin alert for message {message_id}")
                await process_admin_alert_reactions(
                    admin_alert, user_id, added_reactions, removed_reactions,
                    admin_alert_repo, context, config
                )
                return
            else:
                logger.info(f"❌ No admin alert found for message {message_id}")
        
        # Try to find leave request (Attendance & Leave topic)
        attendance_repo = context.bot_data.get('attendance_repository')
        if attendance_repo:
            # Search for leave request by message_id
            try:
                all_pending = await attendance_repo.get_pending_leave_requests()
                leave_request = None
                for req in all_pending:
                    if req.message_id == message_id:
                        leave_request = req
                        break
                
                if leave_request:
                    logger.info(f"✅ Found leave request for message {message_id}")
                    await process_leave_reactions(
                        leave_request, user_id, added_reactions, removed_reactions,
                        attendance_repo, context, config
                    )
                    return
                else:
                    logger.debug(f"❌ No leave request found for message {message_id}")
            except Exception as e:
                logger.warning(f"Error checking for leave request: {e}")
        
        logger.warning(f"⚠️ No task, issue, QA submission, admin alert, or leave request found for message {message_id}")
        
    except Exception as e:
        logger.error(f"Error handling reaction update: {e}", exc_info=True)


async def process_task_reactions(task, user_id, added_reactions, removed_reactions,
                                task_service, context, config):
    """
    Process reactions on task messages with proper state transitions.
    
    State transitions:
    - 👍: ASSIGNED → STARTED (first reaction by assignee)
    - ❤️: QA_SUBMITTED → APPROVED (QA reviewer)
    - 👎: QA_SUBMITTED → REJECTED (QA reviewer)
    - 🔥: Add exemption flag (admin/manager only)
    """
    
    # Build message link for warnings
    group_id_str = str(config.TELEGRAM_GROUP_ID)
    if group_id_str.startswith('-100'):
        group_id_clean = group_id_str[4:]
    else:
        group_id_clean = group_id_str
    task_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_TASK_ALLOCATION}/{task.message_id}"
    
    # Process added reactions
    for emoji in added_reactions:
        try:
            if emoji == "👍":
                # Transition ASSIGNED → STARTED
                if task.state == TaskState.ASSIGNED:
                    # Check if user is the assignee
                    if user_id == task.assignee_id:
                        success = await task_service.state_engine.process_thumbs_up_reaction(
                            task.ticket, user_id, datetime.now()
                        )
                        if success:
                            logger.info(f"✅ Task {task.ticket} transitioned to STARTED by {user_id}")
                            # Record reaction in database
                            await task_service.task_repo.add_reaction(
                                task.ticket, emoji, user_id, task.message_id, task.topic_id
                            )
                            
                            # AUTO CHECK-IN: Mark attendance on first task of the day
                            try:
                                from datetime import date
                                from src.data.repositories.attendance_repository import AttendanceRepository
                                from src.data.models.attendance import Attendance
                                
                                attendance_repo = AttendanceRepository(context.bot_data.get('db_adapter'))
                                today = date.today()
                                
                                # Check if already checked in today
                                existing_attendance = await attendance_repo.get_attendance(user_id, today)
                                
                                if not existing_attendance:
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
                                    
                                    # Get username
                                    user_repo = context.bot_data.get('user_repository')
                                    username = "Unknown"
                                    if user_repo:
                                        user = await user_repo.get_user(user_id)
                                        if user and user.username:
                                            username = user.username
                                    
                                    # Send to Attendance & Leave Control topic
                                    status_text = "⚠️ Late" if is_late else "✅ On-time"
                                    time_str = now.strftime('%I:%M %p')
                                    
                                    attendance_msg = f"""✅ **Check-in Recorded** (Auto)

**Employee:** @{username}
**User ID:** {user_id}
**Time:** {time_str}
**Status:** {status_text}
**Date:** {today.strftime('%Y-%m-%d')}
**Trigger:** First task started"""
                                    
                                    await context.bot.send_message(
                                        chat_id=config.TELEGRAM_GROUP_ID,
                                        text=attendance_msg,
                                        parse_mode='Markdown',
                                        message_thread_id=config.TOPIC_ATTENDANCE_LEAVE
                                    )
                                    
                                    # Send DM confirmation
                                    from src.utils.message_utils import send_auto_delete_dm
                                    await send_auto_delete_dm(
                                        context=context,
                                        user_id=user_id,
                                        text=f"""✅ **Check-in Recorded**

**Time:** {time_str}
**Status:** {status_text}
**Date:** {today.strftime('%Y-%m-%d')}

Have a productive day!""",
                                        delete_after_seconds=60
                                    )
                                    
                                    logger.info(f"✅ Auto check-in recorded for user {user_id} (@{username}) at {time_str} (late={is_late})")
                                else:
                                    logger.debug(f"User {user_id} already checked in today")
                                    
                            except Exception as e:
                                logger.error(f"Error recording auto check-in for user {user_id}: {e}", exc_info=True)
                        else:
                            logger.warning(f"Failed to transition {task.ticket} to STARTED")
                    else:
                        logger.warning(f"User {user_id} is not assignee of task {task.ticket}")
                        await send_invalid_reaction_warning(
                            context, user_id, "👍", "task", f"#{task.ticket}",
                            f"Only the task assignee can start the task.\n\nThis task is assigned to user ID: {task.assignee_id}",
                            task_link
                        )
                else:
                    logger.debug(f"Task {task.ticket} not in ASSIGNED state (current: {task.state})")
                    await send_invalid_reaction_warning(
                        context, user_id, "👍", "task", f"#{task.ticket}",
                        f"This reaction only works when task is in ASSIGNED state.\n\nCurrent state: **{task.state.value}**\n\nThe 👍 reaction is used to start working on a task.",
                        task_link
                    )
            
            elif emoji == "❤️":
                # Two scenarios for heart reaction:
                # 1. QA_SUBMITTED → APPROVED (QA reviewer approves)
                # 2. APPROVED → Mark as complete (Assignee confirms completion)
                
                if task.state == TaskState.QA_SUBMITTED:
                    # QA reviewer approving the task
                    if user_id in config.QA_REVIEWERS:
                        # Check for blocking tasks
                        blocking_tasks = await task_service.task_repo.get_blocking_tasks(task.ticket)
                        if blocking_tasks:
                            logger.warning(f"Task {task.ticket} has blocking tasks: {blocking_tasks}")
                            blocking_list = ", ".join([f"#{t}" for t in blocking_tasks])
                            await send_invalid_reaction_warning(
                                context, user_id, "❤️", "task", f"#{task.ticket}",
                                f"❌ **Task is Blocked**\n\nThis task cannot be approved because it is blocked by:\n{blocking_list}\n\nPlease resolve the blocking tasks first, then try again.",
                                task_link
                            )
                        else:
                            success = await task_service.state_engine.process_heart_reaction(
                                task.ticket, user_id, datetime.now()
                            )
                            if success:
                                logger.info(f"✅ Task {task.ticket} transitioned to APPROVED by {user_id}")
                                await task_service.task_repo.add_reaction(
                                    task.ticket, emoji, user_id, task.message_id, task.topic_id
                                )
                            else:
                                logger.warning(f"Failed to transition {task.ticket} to APPROVED")
                    else:
                        logger.warning(f"User {user_id} is not a QA reviewer")
                        await send_invalid_reaction_warning(
                            context, user_id, "❤️", "task", f"#{task.ticket}",
                            "Only authorized QA reviewers can approve QA submissions.\n\nYou are not in the QA reviewers list.\n\nPlease contact an administrator if you should have QA review access.",
                            task_link
                        )
                
                elif task.state == TaskState.APPROVED:
                    # Assignee confirming task completion
                    if user_id == task.assignee_id:
                        logger.info(f"✅ Assignee {user_id} confirmed completion of task {task.ticket}")
                        # Record the completion confirmation reaction
                        await task_service.task_repo.add_reaction(
                            task.ticket, emoji, user_id, task.message_id, task.topic_id
                        )
                        
                        # Send confirmation to assignee
                        try:
                            from src.utils.message_utils import send_auto_delete_dm
                            await send_auto_delete_dm(
                                context=context,
                                user_id=user_id,
                                text=f"✅ **Completion Confirmed**\n\nYou've marked task **#{task.ticket}** as complete.\n\nThe task will be automatically archived within 24 hours.\n\nThank you for your work!",
                                delete_after_seconds=60
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send completion confirmation: {e}")
                    else:
                        logger.warning(f"User {user_id} is not the assignee of task {task.ticket}")
                        await send_invalid_reaction_warning(
                            context, user_id, "❤️", "task", f"#{task.ticket}",
                            f"Only the task assignee can confirm completion.\n\nThis task is assigned to user ID: {task.assignee_id}",
                            task_link
                        )
                
                else:
                    logger.debug(f"Task {task.ticket} not in QA_SUBMITTED or APPROVED state (current: {task.state})")
                    await send_invalid_reaction_warning(
                        context, user_id, "❤️", "task", f"#{task.ticket}",
                        f"This reaction only works when:\n• Task is in **QA_SUBMITTED** state (for QA reviewers to approve)\n• Task is in **APPROVED** state (for assignees to confirm completion)\n\nCurrent state: **{task.state.value}**\n\nTo mark this task complete, please submit it for QA review first using `/submitqa` command.",
                        task_link
                    )
            
            elif emoji == "👎":
                # Transition QA_SUBMITTED → REJECTED
                if task.state == TaskState.QA_SUBMITTED:
                    # Check if user is QA reviewer
                    if user_id in config.QA_REVIEWERS:
                        success = await task_service.state_engine.process_thumbs_down_reaction(
                            task.ticket, user_id, datetime.now()
                        )
                        if success:
                            logger.info(f"✅ Task {task.ticket} transitioned to REJECTED by {user_id}")
                            await task_service.task_repo.add_reaction(
                                task.ticket, emoji, user_id, task.message_id, task.topic_id
                            )
                        else:
                            logger.warning(f"Failed to transition {task.ticket} to REJECTED")
                    else:
                        logger.warning(f"User {user_id} is not a QA reviewer")
                        await send_invalid_reaction_warning(
                            context, user_id, "👎", "task", f"#{task.ticket}",
                            "Only authorized QA reviewers can reject QA submissions.\n\nYou are not in the QA reviewers list.\n\nPlease contact an administrator if you should have QA review access.",
                            task_link
                        )
                else:
                    logger.debug(f"Task {task.ticket} not in QA_SUBMITTED state (current: {task.state})")
                    await send_invalid_reaction_warning(
                        context, user_id, "👎", "task", f"#{task.ticket}",
                        f"This reaction only works when task is in **QA_SUBMITTED** state.\n\nCurrent state: **{task.state.value}**\n\nThe 👎 reaction is used by QA reviewers to reject QA submissions.",
                        task_link
                    )
            
            elif emoji == "🔥":
                # Add fire exemption (admin/manager only)
                if user_id in config.ADMINISTRATORS or user_id in config.MANAGERS:
                    success = await task_service.state_engine.process_fire_reaction(
                        task.ticket, user_id, datetime.now()
                    )
                    if success:
                        logger.info(f"🔥 Task {task.ticket} marked with exemption by {user_id}")
                        await task_service.task_repo.add_reaction(
                            task.ticket, emoji, user_id, task.message_id, task.topic_id
                        )
                    else:
                        logger.warning(f"Failed to add exemption to {task.ticket}")
                else:
                    logger.warning(f"User {user_id} not authorized for fire exemption")
                    await send_invalid_reaction_warning(
                        context, user_id, "🔥", "task", f"#{task.ticket}",
                        "Only Administrators and Managers can add fire exemptions to tasks.\n\nYou do not have the required permissions.\n\nPlease contact an administrator if this task needs urgent attention.",
                        task_link
                    )
        
        except Exception as e:
            logger.error(f"Error processing {emoji} reaction on task {task.ticket}: {e}", exc_info=True)
    
    # Process removed reactions (state reversion)
    for emoji in removed_reactions:
        try:
            # ALWAYS remove the reaction from database when user removes it
            await task_service.task_repo.remove_reaction(task.ticket, user_id, emoji)
            logger.info(f"🗑️ Removed {emoji} reaction from database for task {task.ticket}")
            
            if emoji == "👍" and task.state == TaskState.STARTED:
                # Revert STARTED → ASSIGNED
                logger.info(f"↩️ Reverting task {task.ticket} from STARTED to ASSIGNED")
                await task_service.task_repo.update_task_state(
                    task.ticket, TaskState.ASSIGNED, datetime.now()
                )
            
            elif emoji == "❤️" and task.state == TaskState.APPROVED:
                # Revert APPROVED → QA_SUBMITTED
                logger.info(f"↩️ Reverting task {task.ticket} from APPROVED to QA_SUBMITTED")
                await task_service.task_repo.update_task_state(
                    task.ticket, TaskState.QA_SUBMITTED, datetime.now()
                )
            
            elif emoji == "👎" and task.state == TaskState.REJECTED:
                # Revert REJECTED → QA_SUBMITTED
                logger.info(f"↩️ Reverting task {task.ticket} from REJECTED to QA_SUBMITTED")
                await task_service.task_repo.update_task_state(
                    task.ticket, TaskState.QA_SUBMITTED, datetime.now()
                )
            
            elif emoji == "🔥":
                # Remove fire exemption
                logger.info(f"↩️ Removing fire exemption from task {task.ticket}")
                await task_service.task_repo.remove_fire_exemption(task.ticket)
        
        except Exception as e:
            logger.error(f"Error removing {emoji} reaction from task {task.ticket}: {e}", exc_info=True)


async def process_issue_reactions(issue, user_id, added_reactions, removed_reactions,
                                 issue_service, context, config):
    """Process reactions on issue messages."""
    
    # Process added reactions
    for emoji in added_reactions:
        try:
            if emoji == "👍":
                # Claim issue
                success = await issue_service.claim_issue(issue.issue_ticket, user_id)
                if success:
                    logger.info(f"👍 User {user_id} claimed issue {issue.issue_ticket}")
                    
                    # Get claimer username
                    user_repo = context.bot_data.get('user_repository')
                    claimer_username = "Someone"
                    if user_repo:
                        claimer = await user_repo.get_user(user_id)
                        if claimer and claimer.username:
                            claimer_username = f"@{claimer.username}"
                    
                    # Build link to issue message
                    from src.utils.link_builder import build_message_link
                    issue_link = build_message_link(config.TELEGRAM_GROUP_ID, issue.message_id)
                    
                    # Send notification to issue creator if different user
                    if issue.creator_id != user_id:
                        try:
                            from src.utils.message_utils import send_auto_delete_dm
                            await send_auto_delete_dm(
                                context=context,
                                user_id=issue.creator_id,
                                text=f"""👍 **Issue Claimed**

Your issue **{issue.issue_ticket}** has been claimed by {claimer_username}.

**Task:** #{issue.ticket}
**Issue:** {issue.title}

[📎 View Issue]({issue_link})""",
                                delete_after_seconds=60
                            )
                            logger.info(f"Sent claim notification to creator {issue.creator_id}")
                        except Exception as e:
                            logger.warning(f"Failed to send claim notification to creator: {e}")
                    
                    # Send notification to task assignee if different from claimer and creator
                    # Get task to find assignee
                    task_service = context.bot_data.get('task_service')
                    if task_service:
                        try:
                            task = await task_service.get_task(issue.ticket)
                            if task and task.assignee_id != user_id and task.assignee_id != issue.creator_id:
                                from src.utils.message_utils import send_auto_delete_dm
                                await send_auto_delete_dm(
                                    context=context,
                                    user_id=task.assignee_id,
                                    text=f"""👍 **Issue Claimed on Your Task**

An issue on your task **#{issue.ticket}** has been claimed by {claimer_username}.

**Issue:** {issue.issue_ticket} - {issue.title}

[📎 View Issue]({issue_link})""",
                                    delete_after_seconds=60
                                )
                                logger.info(f"Sent claim notification to assignee {task.assignee_id}")
                        except Exception as e:
                            logger.warning(f"Failed to send claim notification to assignee: {e}")
            
            elif emoji == "❤️":
                # Resolve issue
                success = await issue_service.resolve_issue(issue.issue_ticket, user_id)
                if success:
                    logger.info(f"❤️ User {user_id} resolved issue {issue.issue_ticket}")
                    
                    # Send DM to issue creator
                    try:
                        from src.utils.message_utils import send_auto_delete_dm
                        await send_auto_delete_dm(
                            context=context,
                            user_id=issue.creator_id,
                            text=f"✅ **Issue Resolved**\n\nIssue **{issue.issue_ticket}** has been resolved.\n\n**Task:** #{issue.ticket}\n**Issue:** {issue.title}",
                            delete_after_seconds=60
                        )
                        logger.info(f"Sent resolution notification to user {issue.creator_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send resolution notification: {e}")
            
            elif emoji == "👎":
                # Reject issue as invalid
                success = await issue_service.reject_issue(issue.issue_ticket, user_id)
                if success:
                    logger.info(f"👎 User {user_id} rejected issue {issue.issue_ticket}")
                    
                    # Send notification to issue creator
                    try:
                        from src.utils.message_utils import send_auto_delete_dm
                        await send_auto_delete_dm(
                            context=context,
                            user_id=issue.creator_id,
                            text=f"❌ **Issue Rejected**\n\nYour issue **{issue.issue_ticket}** has been marked as invalid.\n\n**Task:** #{issue.ticket}\n**Issue:** {issue.title}",
                            delete_after_seconds=60
                        )
                        logger.info(f"Sent rejection notification to user {issue.creator_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send rejection notification: {e}")
        
        except Exception as e:
            logger.error(f"Error processing {emoji} reaction on issue {issue.ticket}: {e}", exc_info=True)
    
    # Process removed reactions
    for emoji in removed_reactions:
        try:
            if emoji == "👍":
                # Remove claim
                success = await issue_service.unclaim_issue(issue.issue_ticket, user_id)
                if success:
                    logger.info(f"↩️ User {user_id} unclaimed issue {issue.issue_ticket}")
                    
                    # Send notification to issue creator if different user
                    if issue.creator_id != user_id:
                        try:
                            await context.bot.send_message(
                                chat_id=issue.creator_id,
                                text=f"↩️ **Issue Unclaimed**\n\nIssue **{issue.issue_ticket}** is no longer claimed.\n\n**Task:** #{issue.ticket}\n**Issue:** {issue.title}",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send unclaim notification: {e}")
        
        except Exception as e:
            logger.error(f"Error removing {emoji} reaction from issue {issue.ticket}: {e}", exc_info=True)


async def process_qa_reactions(qa_submission, user_id, added_reactions, removed_reactions,
                               qa_service, qa_repo, context, config):
    """
    Process reactions on QA submission messages.
    
    Reactions:
    - 👍: Claim as reviewer
    - ❤️: Approve QA submission
    - 👎: Reject QA submission (should use /reject command for reason)
    - 🔥: Escalation flag (auto-added by system)
    """
    
    from src.data.models.qa_submission import QAStatus
    from datetime import datetime
    
    # Build message link for warnings
    group_id_str = str(config.TELEGRAM_GROUP_ID)
    if group_id_str.startswith('-100'):
        group_id_clean = group_id_str[4:]
    else:
        group_id_clean = group_id_str
    qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_submission.message_id}"
    
    # Check if user is the submitter - prevent them from reacting to their own QA
    if user_id == qa_submission.submitter_id and added_reactions:
        # Check if they added any review reactions (not just 🔥 which is system-added)
        review_reactions = added_reactions & {'👍', '❤️', '👎'}
        if review_reactions:
            logger.warning(f"⚠️ Submitter {user_id} tried to react to their own QA {qa_submission.ticket}")
            try:
                from src.utils.message_utils import send_auto_delete_dm
                await send_auto_delete_dm(
                    context=context,
                    user_id=user_id,
                    text=f"⚠️ **Cannot React to Your Own QA**\n\nYou cannot react to your own QA submission for task **#{qa_submission.ticket}**.\n\nOnly reviewers can claim, approve, or reject QA submissions.\n\nPlease wait for a reviewer to process your submission.",
                    delete_after_seconds=30
                )
                logger.info(f"Sent self-reaction warning to submitter {user_id}")
            except Exception as e:
                logger.warning(f"Failed to send self-reaction warning: {e}")
            # Don't process any reactions from the submitter
            return
    
    # Process added reactions
    for emoji in added_reactions:
        try:
            if emoji == "👍":
                # Claim QA for review
                logger.info(f"👍 User {user_id} claimed QA {qa_submission.ticket} for review")
                
                # Send notification to submitter
                try:
                    user_repo = context.bot_data.get('user_repository')
                    reviewer_username = "a reviewer"
                    if user_repo:
                        reviewer = await user_repo.get_user(user_id)
                        if reviewer and reviewer.username:
                            reviewer_username = f"@{reviewer.username}"
                    
                    await context.bot.send_message(
                        chat_id=qa_submission.submitter_id,
                        text=f"👍 **QA Review Started**\n\nYour QA submission for task **#{qa_submission.ticket}** is being reviewed by {reviewer_username}.",
                        parse_mode='Markdown'
                    )
                    logger.info(f"Sent review claim notification to submitter {qa_submission.submitter_id}")
                except Exception as e:
                    logger.warning(f"Failed to send claim notification: {e}")
            
            elif emoji == "❤️":
                # Approve QA submission
                if qa_submission.status != QAStatus.PENDING:
                    logger.warning(f"QA {qa_submission.ticket} is not pending (status: {qa_submission.status})")
                    await send_invalid_reaction_warning(
                        context, user_id, "❤️", "QA submission", f"#{qa_submission.ticket}",
                        f"This reaction only works when QA is in **PENDING** status.\n\nCurrent status: **{qa_submission.status.value}**\n\nThis QA has already been processed.",
                        qa_link
                    )
                    continue
                
                # Check if user is QA reviewer or admin
                if user_id not in config.QA_REVIEWERS and user_id not in config.ADMINISTRATORS and user_id not in config.OWNERS:
                    logger.warning(f"User {user_id} is not authorized to approve QA")
                    await send_invalid_reaction_warning(
                        context, user_id, "❤️", "QA submission", f"#{qa_submission.ticket}",
                        "Only authorized QA reviewers, Administrators, and Owners can approve QA submissions.\n\nYou are not in the authorized list.\n\nPlease contact an administrator if you should have QA review access.",
                        qa_link
                    )
                    continue
                
                # Update QA status to APPROVED
                success = await qa_service.approve_qa(qa_submission.ticket, user_id)
                if success:
                    logger.info(f"❤️ User {user_id} approved QA {qa_submission.ticket}")
                    
                    # Update task state to APPROVED
                    task_service = context.bot_data.get('task_service')
                    if task_service:
                        from src.data.models.task import TaskState
                        await task_service.task_repo.update_task_state(
                            qa_submission.ticket, TaskState.APPROVED, datetime.now()
                        )
                    
                    # Send DM to submitter
                    try:
                        user_repo = context.bot_data.get('user_repository')
                        reviewer_username = "a reviewer"
                        if user_repo:
                            reviewer = await user_repo.get_user(user_id)
                            if reviewer and reviewer.username:
                                reviewer_username = f"@{reviewer.username}"
                        
                        # Build link to QA message
                        group_id_str = str(config.TELEGRAM_GROUP_ID)
                        if group_id_str.startswith('-100'):
                            group_id_clean = group_id_str[4:]
                        else:
                            group_id_clean = group_id_str
                        
                        qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_submission.message_id}"
                        
                        await context.bot.send_message(
                            chat_id=qa_submission.submitter_id,
                            text=f"✅ **QA Approved**\n\nYour QA submission for task **#{qa_submission.ticket}** has been approved by {reviewer_username}.\n\n**Asset:** {qa_submission.asset}\n\n[📎 View QA Submission]({qa_link})\n\nGreat work! The task is now complete.",
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                        logger.info(f"Sent approval notification to submitter {qa_submission.submitter_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send approval notification: {e}")
            
            elif emoji == "👎":
                # Reject QA submission
                # Note: Should use /reject command for proper reason, but allow reaction for quick reject
                if qa_submission.status != QAStatus.PENDING:
                    logger.warning(f"QA {qa_submission.ticket} is not pending (status: {qa_submission.status})")
                    await send_invalid_reaction_warning(
                        context, user_id, "👎", "QA submission", f"#{qa_submission.ticket}",
                        f"This reaction only works when QA is in **PENDING** status.\n\nCurrent status: **{qa_submission.status.value}**\n\nThis QA has already been processed.",
                        qa_link
                    )
                    continue
                
                # Check if user is QA reviewer or admin
                if user_id not in config.QA_REVIEWERS and user_id not in config.ADMINISTRATORS and user_id not in config.OWNERS:
                    logger.warning(f"User {user_id} is not authorized to reject QA")
                    await send_invalid_reaction_warning(
                        context, user_id, "👎", "QA submission", f"#{qa_submission.ticket}",
                        "Only authorized QA reviewers, Administrators, and Owners can reject QA submissions.\n\nYou are not in the authorized list.\n\nPlease contact an administrator if you should have QA review access.",
                        qa_link
                    )
                    continue
                
                # Update QA status to REJECTED
                success = await qa_service.reject_qa(qa_submission.ticket, user_id)
                if success:
                    logger.info(f"👎 User {user_id} rejected QA {qa_submission.ticket}")
                    
                    # Update task state to REJECTED
                    task_service = context.bot_data.get('task_service')
                    if task_service:
                        from src.data.models.task import TaskState
                        await task_service.task_repo.update_task_state(
                            qa_submission.ticket, TaskState.REJECTED, datetime.now()
                        )
                    
                    # Send DM to submitter
                    try:
                        user_repo = context.bot_data.get('user_repository')
                        reviewer_username = "a reviewer"
                        if user_repo:
                            reviewer = await user_repo.get_user(user_id)
                            if reviewer and reviewer.username:
                                reviewer_username = f"@{reviewer.username}"
                        
                        # Build link to QA message
                        group_id_str = str(config.TELEGRAM_GROUP_ID)
                        if group_id_str.startswith('-100'):
                            group_id_clean = group_id_str[4:]
                        else:
                            group_id_clean = group_id_str
                        
                        qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_submission.message_id}"
                        
                        await context.bot.send_message(
                            chat_id=qa_submission.submitter_id,
                            text=f"❌ **QA Rejected**\n\nYour QA submission for task **#{qa_submission.ticket}** has been rejected by {reviewer_username}.\n\n**Asset:** {qa_submission.asset}\n\n[📎 View QA Submission]({qa_link})\n\n⚠️ **Note:** The reviewer should provide feedback via `/reject` command with specific reasons. Please check the QA thread for details or contact the reviewer.",
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                        logger.info(f"Sent rejection notification to submitter {qa_submission.submitter_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send rejection notification: {e}")
            
            elif emoji == "🔥":
                # Escalation flag (usually auto-added by system)
                logger.info(f"🔥 QA {qa_submission.ticket} marked for escalation")
                
                # Notify admins/managers about stale QA
                try:
                    admin_ids = config.ADMINISTRATORS + config.MANAGERS + config.OWNERS
                    for admin_id in admin_ids:
                        try:
                            # Build link to QA message
                            group_id_str = str(config.TELEGRAM_GROUP_ID)
                            if group_id_str.startswith('-100'):
                                group_id_clean = group_id_str[4:]
                            else:
                                group_id_clean = group_id_str
                            
                            qa_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_QA_REVIEW}/{qa_submission.message_id}"
                            
                            await context.bot.send_message(
                                chat_id=admin_id,
                                text=f"🔥 **QA Escalation**\n\nQA submission for task **#{qa_submission.ticket}** has not been reviewed.\n\n**Asset:** {qa_submission.asset}\n**Submitted:** {qa_submission.submitted_at.strftime('%Y-%m-%d %H:%M')}\n\n[📎 View QA Submission]({qa_link})\n\nPlease assign a reviewer or review it yourself.",
                                parse_mode='Markdown',
                                disable_web_page_preview=True
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send escalation notification to admin {admin_id}: {e}")
                except Exception as e:
                    logger.warning(f"Failed to send escalation notifications: {e}")
        
        except Exception as e:
            logger.error(f"Error processing {emoji} reaction on QA {qa_submission.ticket}: {e}", exc_info=True)
    
    # Process removed reactions
    for emoji in removed_reactions:
        try:
            if emoji == "👍":
                # Check if ❤️ or 👎 was ADDED in the same update
                # If yes, this is just Telegram replacing 👍 with ❤️/👎, not an actual unclaim
                if "❤️" in added_reactions or "👎" in added_reactions:
                    logger.info(f"👍 removed but ❤️/👎 added in same update - skipping unclaim notification (this is approval/rejection)")
                    continue
                
                # Fetch latest QA status (might have been updated by added reactions)
                latest_qa = await qa_repo.get_submission_by_message_id(qa_submission.message_id)
                if not latest_qa:
                    logger.warning(f"Could not fetch latest QA for message {qa_submission.message_id}")
                    continue
                
                logger.info(f"👍 removed from QA {latest_qa.ticket} - current status: {latest_qa.status}")
                
                # Only send unclaim notification if QA is still PENDING
                # Don't send if already approved/rejected
                if latest_qa.status == QAStatus.PENDING:
                    # Remove reviewer claim
                    logger.info(f"↩️ User {user_id} unclaimed QA {latest_qa.ticket} - sending unclaim notification")
                    
                    # Send notification to submitter
                    try:
                        await context.bot.send_message(
                            chat_id=latest_qa.submitter_id,
                            text=f"↩️ **QA Review Unclaimed**\n\nQA submission for task **#{latest_qa.ticket}** is no longer being reviewed.\n\nWaiting for another reviewer to claim it.",
                            parse_mode='Markdown'
                        )
                        logger.info(f"Sent unclaim notification to submitter {latest_qa.submitter_id}")
                    except Exception as e:
                        logger.warning(f"Failed to send unclaim notification: {e}")
                else:
                    logger.info(f"Ignoring 👍 removal on QA {latest_qa.ticket} - status is {latest_qa.status}, not PENDING")
            
            elif emoji == "❤️":
                # DO NOT revert approval when ❤️ is removed
                # Once QA is approved, it should stay approved
                # Removing the reaction is just a UI action, not a state change
                logger.debug(f"❤️ removed from QA {qa_submission.ticket} - ignoring (QA stays APPROVED)")
            
            elif emoji == "👎":
                # DO NOT revert rejection when 👎 is removed
                # Once QA is rejected, it should stay rejected
                # Removing the reaction is just a UI action, not a state change
                logger.debug(f"👎 removed from QA {qa_submission.ticket} - ignoring (QA stays REJECTED)")
        
        except Exception as e:
            logger.error(f"Error removing {emoji} reaction from QA {qa_submission.ticket}: {e}", exc_info=True)


async def process_admin_alert_reactions(admin_alert, user_id, added_reactions, removed_reactions,
                                       admin_alert_repo, context, config):
    """
    Process reactions on Admin Control Panel alert messages.
    
    Reactions:
    - 👍: Acknowledge alert (admin has seen it)
    - ❤️: Mark as resolved (admin has handled it)
    """
    
    # Check if user is authorized (admin/manager/owner)
    is_authorized = (
        user_id in config.ADMINISTRATORS or
        user_id in config.MANAGERS or
        user_id in config.OWNERS
    )
    
    if not is_authorized:
        logger.warning(f"User {user_id} not authorized to react to admin alerts")
        # Send warning DM
        try:
            # Build link to admin alert message
            group_id_str = str(config.TELEGRAM_GROUP_ID)
            if group_id_str.startswith('-100'):
                group_id_clean = group_id_str[4:]
            else:
                group_id_clean = group_id_str
            
            alert_link = f"https://t.me/c/{group_id_clean}/{config.TOPIC_ADMIN_CONTROL_PANEL}/{admin_alert.message_id}"
            
            await context.bot.send_message(
                chat_id=user_id,
                text=f"""❌ **Invalid Reaction**

Your reaction on an admin alert was not processed.

**Reason:** Only Administrators, Managers, and Owners can react to admin alerts.

You do not have the required permissions.

[📎 View Alert Message]({alert_link})

**Action Required:** Please remove your reaction from the message.

If you believe you should have admin access, contact a system administrator.""",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            logger.info(f"✉️ Sent unauthorized admin alert reaction warning to user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to send admin alert reaction warning: {e}")
        return
    
    # Process added reactions
    for emoji in added_reactions:
        try:
            if emoji == "👍":
                # Acknowledge alert
                success = await admin_alert_repo.mark_acknowledged(admin_alert.message_id, user_id)
                if success:
                    logger.info(f"👍 User {user_id} acknowledged admin alert {admin_alert.message_id}")
            
            elif emoji == "❤️":
                # Mark as resolved
                success = await admin_alert_repo.mark_resolved(admin_alert.message_id, user_id)
                if success:
                    logger.info(f"❤️ User {user_id} resolved admin alert {admin_alert.message_id}")
        
        except Exception as e:
            logger.error(f"Error processing {emoji} reaction on admin alert {admin_alert.message_id}: {e}", exc_info=True)
    
    # Process removed reactions
    for emoji in removed_reactions:
        try:
            if emoji == "👍":
                # Unmark acknowledgment
                success = await admin_alert_repo.unmark_acknowledged(admin_alert.message_id)
                if success:
                    logger.info(f"↩️ User {user_id} removed acknowledgment from admin alert {admin_alert.message_id}")
            
            elif emoji == "❤️":
                # Unmark resolved
                success = await admin_alert_repo.unmark_resolved(admin_alert.message_id)
                if success:
                    logger.info(f"↩️ User {user_id} removed resolved status from admin alert {admin_alert.message_id}")
        
        except Exception as e:
            logger.error(f"Error removing {emoji} reaction from admin alert {admin_alert.message_id}: {e}", exc_info=True)


def setup_reaction_handlers(application: Application, config: Config):
    """Setup reaction handlers."""
    from telegram.ext import MessageReactionHandler
    
    # Add reaction handler for issue reactions
    application.add_handler(MessageReactionHandler(handle_reaction_update))
    
    logger.info("Reaction handlers registered")


async def process_leave_reactions(leave_request, user_id, added_reactions, removed_reactions,
                                  attendance_repo, context, config):
    """
    Process reactions on leave request messages.
    
    Reactions:
    - 👍: APPROVE leave request (admin/manager/owner only)
    - 👎: REJECT leave request (admin/manager/owner only)
    """
    
    # Permission check - only admins/managers/owners can approve/reject
    is_privileged = (
        user_id in config.ADMINISTRATORS or
        user_id in config.MANAGERS or
        user_id in config.OWNERS
    )
    
    if not is_privileged:
        logger.warning(f"User {user_id} tried to approve/reject leave request without permission")
        await send_invalid_reaction_warning(
            context, user_id, "reaction", "leave request", f"#{leave_request.id}",
            "Only Administrators, Managers, and Owners can approve or reject leave requests."
        )
        return
    
    # Process added reactions
    for emoji in added_reactions:
        try:
            if emoji == "👍":
                # Approve leave request
                leave_service = context.bot_data.get('leave_request_service')
                if leave_service:
                    success, message = await leave_service.approve_leave_request(
                        leave_request.id,
                        user_id
                    )
                    
                    if success:
                        logger.info(f"✅ Approved leave request {leave_request.id}")
                        
                        # Send DM to employee
                        from src.utils.message_utils import send_auto_delete_dm
                        employee = await context.bot_data.get('user_repository').get_user(leave_request.user_id)
                        
                        duration = (leave_request.end_date - leave_request.start_date).days + 1
                        dm_text = f"""✅ **Leave Approved**

**Dates:** {leave_request.start_date} to {leave_request.end_date}
**Duration:** {duration} days
**Reason:** {leave_request.reason}

Your leave request has been approved. You are now marked as on leave."""
                        
                        if leave_request.replacement_user_id:
                            replacement = await context.bot_data.get('user_repository').get_user(leave_request.replacement_user_id)
                            dm_text += f"\n\n**Replacement:** @{replacement.username if replacement else 'Unknown'} will handle your tasks."
                        
                        try:
                            await send_auto_delete_dm(
                                context=context,
                                user_id=leave_request.user_id,
                                text=dm_text,
                                delete_after_seconds=120
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send approval DM to user {leave_request.user_id}: {e}")
                        
                        # Update message in topic
                        try:
                            await context.bot.edit_message_text(
                                chat_id=config.TELEGRAM_GROUP_ID,
                                message_id=leave_request.message_id,
                                text=f"""📋 **Leave Request**

**Employee:** @{employee.username if employee else 'Unknown'}
**User ID:** {leave_request.user_id}
**Dates:** {leave_request.start_date} to {leave_request.end_date}
**Duration:** {duration} days
**Reason:** {leave_request.reason}
**Status:** ✅ APPROVED

Approved by: @{(await context.bot_data.get('user_repository').get_user(user_id)).username if user_id else 'Unknown'}""",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.warning(f"Failed to update leave request message: {e}")
                    else:
                        logger.warning(f"Failed to approve leave request: {message}")
            
            elif emoji == "👎":
                # Reject leave request
                leave_service = context.bot_data.get('leave_request_service')
                if leave_service:
                    success, message = await leave_service.reject_leave_request(
                        leave_request.id,
                        user_id
                    )
                    
                    if success:
                        logger.info(f"✅ Rejected leave request {leave_request.id}")
                        
                        # Send DM to employee
                        from src.utils.message_utils import send_auto_delete_dm
                        employee = await context.bot_data.get('user_repository').get_user(leave_request.user_id)
                        
                        dm_text = f"""❌ **Leave Rejected**

**Dates:** {leave_request.start_date} to {leave_request.end_date}
**Reason:** {leave_request.reason}

Your leave request has been rejected. Please contact your manager for more information."""
                        
                        try:
                            await send_auto_delete_dm(
                                context=context,
                                user_id=leave_request.user_id,
                                text=dm_text,
                                delete_after_seconds=120
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send rejection DM to user {leave_request.user_id}: {e}")
                        
                        # Update message in topic
                        try:
                            duration = (leave_request.end_date - leave_request.start_date).days + 1
                            await context.bot.edit_message_text(
                                chat_id=config.TELEGRAM_GROUP_ID,
                                message_id=leave_request.message_id,
                                text=f"""📋 **Leave Request**

**Employee:** @{employee.username if employee else 'Unknown'}
**User ID:** {leave_request.user_id}
**Dates:** {leave_request.start_date} to {leave_request.end_date}
**Duration:** {duration} days
**Reason:** {leave_request.reason}
**Status:** ❌ REJECTED

Rejected by: @{(await context.bot_data.get('user_repository').get_user(user_id)).username if user_id else 'Unknown'}""",
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.warning(f"Failed to update leave request message: {e}")
                    else:
                        logger.warning(f"Failed to reject leave request: {message}")
        
        except Exception as e:
            logger.error(f"Error processing {emoji} reaction on leave request: {e}", exc_info=True)


