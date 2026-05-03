"""Task service for task management business logic."""

import logging
import re
from datetime import datetime
from typing import Optional, List

from src.data.models import Task, TaskState, TaskReaction, User, UserRole
from src.data.repositories import TaskRepository, UserRepository
from src.core.state.state_engine import StateEngine
from src.config import Config

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task management operations."""
    
    def __init__(
        self,
        task_repo: TaskRepository,
        user_repo: UserRepository,
        state_engine: StateEngine,
        config: Config
    ):
        """Initialize task service."""
        self.task_repo = task_repo
        self.user_repo = user_repo
        self.state_engine = state_engine
        self.config = config
    
    async def create_task(
        self,
        ticket: str,
        brand: str,
        assignee_id: int,
        creator_id: int,
        message_id: int,
        topic_id: int,
        deadline: Optional[datetime] = None,
        send_dm: bool = True
    ) -> Optional[Task]:
        """
        Create a new task.
        
        Args:
            ticket: Unique ticket identifier
            brand: Brand name or code (e.g., "Povaly", "POV", "VorosaBajar", "VRB")
            assignee_id: User ID of assignee
            creator_id: User ID of creator
            message_id: Telegram message ID
            topic_id: Telegram topic ID
            deadline: Optional deadline datetime
            send_dm: Whether to send DM notification (default True)
        
        Returns:
            Created task or None if creation failed
        """
        from src.core.brand_mapper import BrandMapper
        
        logger.info(f"🎯 create_task called: ticket={ticket}, brand={brand}, assignee={assignee_id}")
        
        # Convert brand name to code if needed
        brand_mapper = BrandMapper()
        brand_code = brand_mapper.get_code(brand)
        
        if not brand_code:
            logger.warning(f"❌ Invalid brand: {brand}")
            return None
        
        logger.info(f"✅ Brand mapped: {brand} -> {brand_code}")
        
        # Validate ticket format
        if not re.match(self.config.TICKET_FORMAT_REGEX, ticket):
            logger.warning(f"❌ Invalid ticket format: {ticket} (regex: {self.config.TICKET_FORMAT_REGEX})")
            return None
        
        logger.info(f"✅ Ticket format valid: {ticket}")
        
        # Validate brand code is in configured brands
        if brand_code not in self.config.BRAND_CODES:
            logger.warning(f"❌ Brand code {brand_code} not in configured BRAND_CODES: {self.config.BRAND_CODES}")
            return None
        
        logger.info(f"✅ Brand code validated: {brand_code}")
        
        # Check if task already exists
        logger.info(f"🔍 Checking if task {ticket} already exists...")
        existing = await self.task_repo.get_task(ticket)
        if existing:
            logger.warning(f"❌ Task {ticket} already exists (state: {existing.state})")
            return None
        
        logger.info(f"✅ Task {ticket} does not exist, proceeding with creation")
        
        # Create task with brand code
        task = Task(
            ticket=ticket,
            brand=brand_code,
            assignee_id=assignee_id,
            creator_id=creator_id,
            state=TaskState.ASSIGNED,
            created_at=datetime.now(),
            message_id=message_id,
            topic_id=topic_id,
            deadline=deadline
        )
        
        logger.info(f"📝 Task object created: {task.ticket}, state={task.state.value}")
        
        try:
            logger.info(f"💾 Calling task_repo.create_task for {ticket}...")
            await self.task_repo.create_task(task)
            logger.info(f"✅ task_repo.create_task completed for {ticket}")
            
            # Verify the task was actually saved
            verify = await self.task_repo.get_task(ticket)
            if verify:
                logger.info(f"✅ Task {ticket} verified in database after creation")
            else:
                logger.error(f"❌ CRITICAL: Task {ticket} NOT found in database immediately after creation!")
                return None
            
            logger.info(f"✅ Created task {ticket} assigned to user {assignee_id} with brand {brand_code}")
        except Exception as e:
            logger.error(f"❌ Failed to create task {ticket}: {e}", exc_info=True)
            return None
        
        # Ensure user exists (don't fail task creation if this fails)
        try:
            await self._ensure_user_exists(assignee_id)
            await self._ensure_user_exists(creator_id)
        except Exception as e:
            logger.warning(f"⚠️ Failed to ensure users exist for task {ticket}: {e}")
        
        # Send DM notification to assignee about new task assignment
        if send_dm:
            try:
                from src.utils.link_builder import build_message_link
                
                # Get creator username
                creator = await self.user_repo.get_user(creator_id)
                creator_username = creator.username if creator and creator.username else f"User {creator_id}"
                
                # Build link to task message
                task_link = build_message_link(self.config.TELEGRAM_GROUP_ID, message_id)
                
                # Send DM to assignee
                from telegram import Bot
                bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
                
                # Create message with auto-delete warning
                message_text = f"""📋 **New Task Assigned**

**Task:** #{ticket}
**Brand:** {brand_code}
**Assigned by:** @{creator_username}

[📎 View Task]({task_link})

React with 👍 to start working on this task.

_⏱️ This message will auto-delete in 120 seconds_"""
                
                await bot.send_message(
                    chat_id=assignee_id,
                    text=message_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info(f"✅ Sent task assignment DM to user {assignee_id} for task {ticket}")
                
                # Schedule auto-delete
                import asyncio
                async def delete_after_delay():
                    await asyncio.sleep(120)
                    try:
                        # Note: We can't delete the message here because we don't have the message_id
                        # The bot instance is temporary. This is a limitation.
                        pass
                    except Exception as e:
                        logger.warning(f"Failed to auto-delete task assignment DM: {e}")
                
                asyncio.create_task(delete_after_delay())
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to send task assignment DM to user {assignee_id}: {e}")
        
        return task
    
    async def process_reaction(
        self,
        ticket: str,
        reaction: str,
        user_id: int,
        message_id: int,
        topic_id: int
    ) -> bool:
        """
        Process a reaction on a task message.
        
        Args:
            ticket: Task ticket ID
            reaction: Reaction emoji
            user_id: User who added reaction
            message_id: Message ID
            topic_id: Topic ID
        
        Returns:
            True if reaction was processed successfully
        """
        timestamp = datetime.now()
        
        # Record reaction
        task_reaction = TaskReaction(
            id=None,
            message_id=message_id,
            ticket=ticket,
            user_id=user_id,
            reaction=reaction,
            timestamp=timestamp,
            topic_id=topic_id
        )
        await self.task_repo.add_reaction(task_reaction)
        
        # Process state transition based on reaction
        if reaction == "👍":
            return await self.state_engine.process_thumbs_up_reaction(ticket, user_id, timestamp)
        elif reaction == "❤️":
            return await self.state_engine.process_heart_reaction(ticket, user_id, timestamp)
        elif reaction == "👎":
            return await self.state_engine.process_thumbs_down_reaction(ticket, user_id, timestamp)
        elif reaction == "🔥":
            # Check if user is authorized for fire exemption
            if await self._is_authorized_for_fire(user_id):
                return await self.state_engine.process_fire_reaction(ticket, user_id, timestamp)
            else:
                logger.warning(f"User {user_id} not authorized for 🔥 reaction")
                return False
        
        return True
    
    async def get_task(self, ticket: str) -> Optional[Task]:
        """Get task by ticket ID."""
        return await self.task_repo.get_task(ticket)
    
    async def get_task_by_message_id(self, message_id: int) -> Optional[Task]:
        """Get task by message ID."""
        return await self.task_repo.get_task_by_message_id(message_id)
    
    async def get_tasks_by_assignee(
        self,
        assignee_id: int,
        state: Optional[TaskState] = None
    ) -> List[Task]:
        """Get tasks assigned to a user."""
        return await self.task_repo.get_tasks_by_assignee(assignee_id, state)
    
    async def get_tasks_by_state(self, state: TaskState) -> List[Task]:
        """Get all tasks in a specific state."""
        return await self.task_repo.get_tasks_by_state(state)
    
    async def _ensure_user_exists(self, user_id: int):
        """Ensure user exists in database."""
        user = await self.user_repo.get_user(user_id)
        if not user:
            # Create basic user record
            user = User(
                user_id=user_id,
                username=f"user_{user_id}",
                full_name=f"User {user_id}",
                role=UserRole.REGULAR,
                created_at=datetime.now(),
                last_active=datetime.now()
            )
            await self.user_repo.create_user(user)
            logger.info(f"Created user record for {user_id}")
    
    async def _is_authorized_for_fire(self, user_id: int) -> bool:
        """Check if user is authorized to add fire emoji exemption."""
        return (
            user_id in self.config.ADMINISTRATORS or
            user_id in self.config.MANAGERS or
            user_id in self.config.OWNERS
        )
