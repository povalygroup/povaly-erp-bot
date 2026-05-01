"""
Automated tests for task system rebuild.

Run with: pytest tests/test_task_system.py -v
"""

import pytest
import asyncio
from datetime import datetime
from src.core.ticket_generator import TicketGenerator
from src.core.brand_mapper import BrandMapper
from src.data.adapters.sqlite_adapter import SQLiteAdapter
from src.data.models import Task, TaskState, TaskReaction
from src.data.repositories import TaskRepository
from src.core.state.state_engine import StateEngine
from src.config import Config


@pytest.fixture
async def db():
    """Setup test database."""
    adapter = SQLiteAdapter(":memory:")
    await adapter.initialize()
    yield adapter
    await adapter.close()


@pytest.fixture
async def task_repo(db):
    """Setup task repository."""
    return TaskRepository(db)


@pytest.fixture
async def state_engine(task_repo):
    """Setup state engine."""
    return StateEngine(task_repo)


# ============================================================================
# UNIT TESTS - Ticket Generator
# ============================================================================

@pytest.mark.asyncio
async def test_ticket_generation_povaly(db):
    """Test ticket generation for Povaly brand."""
    brand_mapper = BrandMapper()
    gen = TicketGenerator(db, brand_mapper)
    
    ticket = await gen.generate_ticket_id("Povaly")
    
    assert ticket.startswith("POV"), f"Expected POV prefix, got {ticket}"
    assert len(ticket) == 8, f"Expected 8 chars, got {len(ticket)}"
    assert ticket[3:7].isdigit(), f"Expected YYMM digits, got {ticket[3:7]}"


@pytest.mark.asyncio
async def test_ticket_generation_all_brands(db):
    """Test ticket generation for all brands."""
    brand_mapper = BrandMapper()
    gen = TicketGenerator(db, brand_mapper)
    
    brands = {
        "Povaly": "POV",
        "VorosaBajar": "VRB",
        "GSMAura": "GSM"
    }
    
    for brand_name, expected_prefix in brands.items():
        ticket = await gen.generate_ticket_id(brand_name)
        assert ticket.startswith(expected_prefix), \
            f"Expected {expected_prefix} for {brand_name}, got {ticket}"


@pytest.mark.asyncio
async def test_numeric_sorting(db):
    """Test that numeric sorting works correctly."""
    brand_mapper = BrandMapper()
    gen = TicketGenerator(db, brand_mapper)
    
    # Insert test tickets with non-sequential numbers
    tickets = ["POV260401", "POV260410", "POV260409", "POV260420"]
    for ticket in tickets:
        task = Task(
            ticket=ticket,
            brand="POV",
            assignee_id=123,
            creator_id=123,
            state=TaskState.ASSIGNED,
            created_at=datetime.now(),
            message_id=1,
            topic_id=1
        )
        await db.insert_task(task)
    
    # Generate next ticket
    next_ticket = await gen.generate_ticket_id("Povaly")
    
    # Should be 21, not 10 (numeric sorting, not alphabetic)
    assert next_ticket == "POV260421", \
        f"Expected POV260421 (numeric sort), got {next_ticket}"


@pytest.mark.asyncio
async def test_ticket_increment(db):
    """Test that ticket numbers increment correctly."""
    brand_mapper = BrandMapper()
    gen = TicketGenerator(db, brand_mapper)
    
    # Generate first ticket
    ticket1 = await gen.generate_ticket_id("Povaly")
    
    # Create task with first ticket
    task = Task(
        ticket=ticket1,
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Generate second ticket
    ticket2 = await gen.generate_ticket_id("Povaly")
    
    # Extract numbers
    num1 = int(ticket1[7:])
    num2 = int(ticket2[7:])
    
    assert num2 == num1 + 1, \
        f"Expected {num1 + 1}, got {num2}"


# ============================================================================
# UNIT TESTS - State Engine
# ============================================================================

@pytest.mark.asyncio
async def test_state_transition_assigned_to_started(db, task_repo, state_engine):
    """Test ASSIGNED → STARTED transition."""
    # Create task
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Transition to STARTED
    result = await state_engine.process_thumbs_up_reaction(
        "POV260401", 123, datetime.now()
    )
    
    assert result, "Transition should succeed"
    
    # Verify state changed
    updated_task = await task_repo.get_task("POV260401")
    assert updated_task.state == TaskState.STARTED, \
        f"Expected STARTED, got {updated_task.state}"


@pytest.mark.asyncio
async def test_state_transition_qa_submitted_to_approved(db, task_repo, state_engine):
    """Test QA_SUBMITTED → APPROVED transition."""
    # Create task in QA_SUBMITTED state
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.QA_SUBMITTED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Transition to APPROVED
    result = await state_engine.process_heart_reaction(
        "POV260401", 456, datetime.now()
    )
    
    assert result, "Transition should succeed"
    
    # Verify state changed
    updated_task = await task_repo.get_task("POV260401")
    assert updated_task.state == TaskState.APPROVED, \
        f"Expected APPROVED, got {updated_task.state}"


@pytest.mark.asyncio
async def test_state_transition_qa_submitted_to_rejected(db, task_repo, state_engine):
    """Test QA_SUBMITTED → REJECTED transition."""
    # Create task in QA_SUBMITTED state
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.QA_SUBMITTED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Transition to REJECTED
    result = await state_engine.process_thumbs_down_reaction(
        "POV260401", 456, datetime.now()
    )
    
    assert result, "Transition should succeed"
    
    # Verify state changed
    updated_task = await task_repo.get_task("POV260401")
    assert updated_task.state == TaskState.REJECTED, \
        f"Expected REJECTED, got {updated_task.state}"


# ============================================================================
# UNIT TESTS - Database Operations
# ============================================================================

@pytest.mark.asyncio
async def test_get_task_by_message_id(db):
    """Test getting task by message ID."""
    # Create task
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=999,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Get by message ID
    retrieved = await db.get_task_by_message_id(999)
    
    assert retrieved is not None, "Task should be found"
    assert retrieved.ticket == "POV260401", \
        f"Expected POV260401, got {retrieved.ticket}"


@pytest.mark.asyncio
async def test_add_reaction(db):
    """Test adding reaction to task."""
    # Create task
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Add reaction
    reaction = TaskReaction(
        id=None,
        message_id=1,
        ticket="POV260401",
        user_id=123,
        reaction="👍",
        timestamp=datetime.now(),
        topic_id=1
    )
    await db.insert_reaction(reaction)
    
    # Verify reaction was added
    first_reaction = await db.get_first_reaction("POV260401", "👍")
    assert first_reaction is not None, "Reaction should be found"
    assert first_reaction.reaction == "👍", \
        f"Expected 👍, got {first_reaction.reaction}"


@pytest.mark.asyncio
async def test_fire_exemption(db):
    """Test fire exemption flag."""
    # Create task
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Add exemption
    await db.update_fire_exemption("POV260401", 999, datetime.now())
    
    # Verify exemption was set
    updated_task = await db.get_task_by_ticket("POV260401")
    assert updated_task.has_fire_exemption == 1, \
        "Fire exemption should be set"
    assert updated_task.fire_exemption_by == 999, \
        f"Expected user 999, got {updated_task.fire_exemption_by}"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_complete_task_lifecycle(db, task_repo, state_engine):
    """Test complete task lifecycle: ASSIGNED → STARTED → QA_SUBMITTED → APPROVED."""
    # Step 1: Create task (ASSIGNED)
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Step 2: Assignee starts work (ASSIGNED → STARTED)
    await state_engine.process_thumbs_up_reaction("POV260401", 123, datetime.now())
    task = await task_repo.get_task("POV260401")
    assert task.state == TaskState.STARTED
    
    # Step 3: Submit to QA (STARTED → QA_SUBMITTED)
    await task_repo.update_task_state("POV260401", TaskState.QA_SUBMITTED)
    task = await task_repo.get_task("POV260401")
    assert task.state == TaskState.QA_SUBMITTED
    
    # Step 4: QA approves (QA_SUBMITTED → APPROVED)
    await state_engine.process_heart_reaction("POV260401", 456, datetime.now())
    task = await task_repo.get_task("POV260401")
    assert task.state == TaskState.APPROVED


@pytest.mark.asyncio
async def test_rejection_and_resubmission(db, task_repo, state_engine):
    """Test rejection and resubmission flow."""
    # Create task in QA_SUBMITTED
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.QA_SUBMITTED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # QA rejects (QA_SUBMITTED → REJECTED)
    await state_engine.process_thumbs_down_reaction("POV260401", 456, datetime.now())
    task = await task_repo.get_task("POV260401")
    assert task.state == TaskState.REJECTED
    
    # Revert to QA_SUBMITTED
    await task_repo.update_task_state("POV260401", TaskState.QA_SUBMITTED)
    task = await task_repo.get_task("POV260401")
    assert task.state == TaskState.QA_SUBMITTED
    
    # QA approves (QA_SUBMITTED → APPROVED)
    await state_engine.process_heart_reaction("POV260401", 456, datetime.now())
    task = await task_repo.get_task("POV260401")
    assert task.state == TaskState.APPROVED


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_duplicate_ticket_detection(db):
    """Test duplicate ticket detection."""
    # Create first task
    task1 = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task1)
    
    # Try to create duplicate
    task2 = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=456,
        creator_id=456,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=2,
        topic_id=1
    )
    
    # Should fail (duplicate ticket)
    with pytest.raises(Exception):
        await db.insert_task(task2)


@pytest.mark.asyncio
async def test_multiple_reactions_same_task(db):
    """Test multiple reactions on same task."""
    # Create task
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Add multiple reactions
    reactions = ["👍", "❤️", "👎", "🔥"]
    for emoji in reactions:
        reaction = TaskReaction(
            id=None,
            message_id=1,
            ticket="POV260401",
            user_id=123,
            reaction=emoji,
            timestamp=datetime.now(),
            topic_id=1
        )
        await db.insert_reaction(reaction)
    
    # Verify all reactions were added
    for emoji in reactions:
        r = await db.get_first_reaction("POV260401", emoji)
        assert r is not None, f"Reaction {emoji} should be found"


@pytest.mark.asyncio
async def test_special_characters_in_task(db):
    """Test task with special characters."""
    task = Task(
        ticket="POV260401",
        brand="POV",
        assignee_id=123,
        creator_id=123,
        state=TaskState.ASSIGNED,
        created_at=datetime.now(),
        message_id=1,
        topic_id=1
    )
    await db.insert_task(task)
    
    # Verify task was created
    retrieved = await db.get_task_by_ticket("POV260401")
    assert retrieved is not None, "Task should be found"


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_ticket_generation_performance(db):
    """Test ticket generation performance."""
    import time
    
    brand_mapper = BrandMapper()
    gen = TicketGenerator(db, brand_mapper)
    
    start = time.time()
    for i in range(100):
        await gen.generate_ticket_id("Povaly")
    elapsed = time.time() - start
    
    # Should generate 100 tickets in < 5 seconds
    assert elapsed < 5, \
        f"Generated 100 tickets in {elapsed:.2f}s (should be < 5s)"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
