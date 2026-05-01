"""Simple test script to verify bot setup."""

import asyncio
from datetime import datetime
from src.config import get_config
from src.data.adapters.factory import create_database_adapter
from src.data.models import Task, TaskState


async def test_database():
    """Test database operations."""
    print("🧪 Testing database...")
    
    # Load config
    config = get_config()
    print(f"✅ Config loaded: {config.DATABASE_TYPE}")
    
    # Initialize database
    db = create_database_adapter(config)
    await db.initialize()
    print("✅ Database initialized")
    
    # Create a test task
    task = Task(
        ticket="TEST-0101-1",
        brand="TEST",
        assignee_id=123456,
        creator_id=789012,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=4
    )
    
    await db.insert_task(task)
    print(f"✅ Task created: {task.ticket}")
    
    # Retrieve task
    retrieved = await db.get_task_by_ticket("TEST-0101-1")
    print(f"✅ Task retrieved: {retrieved.ticket} - State: {retrieved.state.value}")
    
    # Update state
    await db.update_task_state("TEST-0101-1", TaskState.STARTED)
    updated = await db.get_task_by_ticket("TEST-0101-1")
    print(f"✅ Task state updated: {updated.state.value}")
    
    await db.close()
    print("✅ Database test passed!")


if __name__ == "__main__":
    asyncio.run(test_database())
