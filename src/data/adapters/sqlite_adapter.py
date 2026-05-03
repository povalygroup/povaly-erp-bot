# Copy this entire content to: src/data/adapters/sqlite_adapter.py

"""SQLite database adapter implementation."""

import aiosqlite
import json
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime, date

from src.data.models import (
    Task, TaskState, TaskReaction, RejectFeedback, Archive,
    User, UserRole, QASubmission, QAStatus,
    Attendance, LeaveRequest, LeaveStatus,
    Report, ReportType, Violation, ViolationType,
    AuditTrail, EventType
)

logger = logging.getLogger(__name__)


class SQLiteAdapter:
    """SQLite database adapter implementation."""
    
    def __init__(self, db_path: str):
        """Initialize SQLite adapter."""
        self.db_path = db_path
        self.conn = None
    
    async def initialize(self):
        """Initialize database connection and create tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        
        # Enable foreign key constraints
        await self.conn.execute("PRAGMA foreign_keys = ON")
        
        await self._create_tables()
        await self._run_migrations()
        print(f"✅ Database initialized: {self.db_path}")
    
    async def _create_tables(self):
        """Create all database tables."""
        
        # Schema version tracking
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
        """)
        
        # Users table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                is_on_leave INTEGER DEFAULT 0,
                leave_start TEXT,
                leave_end TEXT
            )
        """)
        
        # Tasks table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                ticket TEXT PRIMARY KEY,
                brand TEXT NOT NULL,
                assignee_id INTEGER NOT NULL,
                creator_id INTEGER NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                qa_submitted_at TEXT,
                completed_at TEXT,
                message_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                has_fire_exemption INTEGER DEFAULT 0,
                fire_exemption_by INTEGER,
                fire_exemption_at TEXT,
                FOREIGN KEY(creator_id) REFERENCES users(user_id)
            )
        """)
        
        # Task Assignees table (multiple assignees per task)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS task_assignees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket TEXT NOT NULL,
                assignee_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'ASSIGNED',
                assigned_at TEXT NOT NULL,
                acknowledged_at TEXT,
                started_at TEXT,
                submitted_at TEXT,
                completed_at TEXT,
                is_primary INTEGER DEFAULT 0,
                UNIQUE(ticket, assignee_id),
                FOREIGN KEY(ticket) REFERENCES tasks(ticket) ON DELETE CASCADE,
                FOREIGN KEY(assignee_id) REFERENCES users(user_id)
            )
        """)
        
        # Task Reactions table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS task_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                ticket TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                reaction TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                topic_id INTEGER NOT NULL,
                context TEXT,
                removed_at TEXT,
                FOREIGN KEY(ticket) REFERENCES tasks(ticket) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # Reject Feedback table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reject_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                problem TEXT NOT NULL,
                fix_required TEXT NOT NULL,
                assignee_id INTEGER NOT NULL,
                reviewer_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                FOREIGN KEY(ticket) REFERENCES tasks(ticket) ON DELETE CASCADE,
                FOREIGN KEY(assignee_id) REFERENCES users(user_id),
                FOREIGN KEY(reviewer_id) REFERENCES users(user_id)
            )
        """)
        
        # Archive table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket TEXT NOT NULL,
                assignee_id INTEGER NOT NULL,
                qa_reviewer_id INTEGER NOT NULL,
                archived_at TEXT NOT NULL,
                original_message_id INTEGER NOT NULL,
                qa_message_id INTEGER NOT NULL,
                archive_message_id INTEGER NOT NULL,
                completion_time_hours REAL NOT NULL,
                FOREIGN KEY(ticket) REFERENCES tasks(ticket),
                FOREIGN KEY(assignee_id) REFERENCES users(user_id),
                FOREIGN KEY(qa_reviewer_id) REFERENCES users(user_id)
            )
        """)
        
        # QA Submissions table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket TEXT NOT NULL,
                brand TEXT NOT NULL,
                asset TEXT NOT NULL,
                submitter_id INTEGER NOT NULL,
                submitted_at TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                status TEXT DEFAULT 'PENDING',
                reviewed_by INTEGER,
                reviewed_at TEXT,
                FOREIGN KEY(ticket) REFERENCES tasks(ticket) ON DELETE CASCADE,
                FOREIGN KEY(submitter_id) REFERENCES users(user_id),
                FOREIGN KEY(reviewed_by) REFERENCES users(user_id)
            )
        """)
        
        # QA Reviewers table (multiple reviewers per QA submission)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_reviewers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qa_submission_id INTEGER NOT NULL,
                reviewer_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'ASSIGNED',
                assigned_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                rejection_reason TEXT,
                rejection_feedback TEXT,
                is_primary INTEGER DEFAULT 0,
                UNIQUE(qa_submission_id, reviewer_id),
                FOREIGN KEY(qa_submission_id) REFERENCES qa_submissions(id) ON DELETE CASCADE,
                FOREIGN KEY(reviewer_id) REFERENCES users(user_id)
            )
        """)
        
        # QA Reactions table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qa_submission_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                reaction TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                context TEXT,
                reacted_at TEXT NOT NULL,
                removed_at TEXT,
                FOREIGN KEY(qa_submission_id) REFERENCES qa_submissions(id) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # Issues table (Core Operations)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                ticket TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                details TEXT NOT NULL,
                priority TEXT NOT NULL,
                assignee_username TEXT,
                creator_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL,
                claimed_at TEXT,
                resolved_at TEXT,
                escalated_at TEXT,
                claimed_by TEXT DEFAULT '',
                resolved_by INTEGER,
                rejected_by INTEGER,
                escalation_sent INTEGER DEFAULT 0,
                reminder_sent INTEGER DEFAULT 0,
                FOREIGN KEY(creator_id) REFERENCES users(user_id)
            )
        """)
        
        # Issue Handlers table (multiple handlers per issue)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS issue_handlers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_ticket TEXT NOT NULL,
                handler_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'CLAIMED',
                claimed_at TEXT NOT NULL,
                started_at TEXT,
                resolved_at TEXT,
                is_primary INTEGER DEFAULT 0,
                UNIQUE(issue_ticket, handler_id),
                FOREIGN KEY(issue_ticket) REFERENCES issues(ticket) ON DELETE CASCADE,
                FOREIGN KEY(handler_id) REFERENCES users(user_id)
            )
        """)
        
        # Issue Reactions table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS issue_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_ticket TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                reaction TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                context TEXT,
                reacted_at TEXT NOT NULL,
                removed_at TEXT,
                FOREIGN KEY(issue_ticket) REFERENCES issues(ticket) ON DELETE CASCADE,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # Attendance table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                checkin_time TEXT NOT NULL,
                checkout_time TEXT,
                is_late INTEGER DEFAULT 0,
                is_auto_checkout INTEGER DEFAULT 0,
                total_hours REAL,
                UNIQUE(user_id, date),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # Leave Requests table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                requested_at TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                reviewed_by INTEGER,
                reviewed_at TEXT,
                replacement_user_id INTEGER,
                task_handover_ids TEXT,
                is_notified INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(reviewed_by) REFERENCES users(user_id),
                FOREIGN KEY(replacement_user_id) REFERENCES users(user_id)
            )
        """)
        
        # Reports table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                date TEXT NOT NULL,
                content TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                generated_at TEXT NOT NULL,
                user_id INTEGER,
                metrics TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # Violations table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                violation_type TEXT NOT NULL,
                description TEXT NOT NULL,
                context TEXT NOT NULL,
                detected_at TEXT NOT NULL,
                action_taken TEXT NOT NULL,
                message_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # Audit Trail table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                context TEXT NOT NULL,
                user_id INTEGER,
                ticket TEXT,
                before_state TEXT,
                after_state TEXT,
                message_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        # Ticket Audit Trail table (detailed ticket-specific audit)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ticket_audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket TEXT NOT NULL,
                action TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_by INTEGER NOT NULL,
                changed_at TEXT NOT NULL,
                context TEXT,
                FOREIGN KEY(ticket) REFERENCES tasks(ticket) ON DELETE CASCADE,
                FOREIGN KEY(changed_by) REFERENCES users(user_id)
            )
        """)
        
        # Ticket Metadata table (custom fields)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ticket_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                set_at TEXT NOT NULL,
                set_by INTEGER,
                UNIQUE(ticket, key),
                FOREIGN KEY(ticket) REFERENCES tasks(ticket) ON DELETE CASCADE,
                FOREIGN KEY(set_by) REFERENCES users(user_id)
            )
        """)
        
        # Create task_dependencies table
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket TEXT NOT NULL,
                blocked_by_ticket TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                created_by INTEGER NOT NULL,
                FOREIGN KEY (ticket) REFERENCES tasks(ticket) ON DELETE CASCADE,
                FOREIGN KEY (blocked_by_ticket) REFERENCES tasks(ticket) ON DELETE CASCADE,
                UNIQUE(ticket, blocked_by_ticket)
            )
        """)
        
        # Create indexes for performance
        await self._create_indexes()
        
        await self.conn.commit()
    
    async def _create_indexes(self):
        """Create database indexes for performance."""
        indexes = [
            # Task indexes
            ("idx_tasks_assignee", "tasks", "assignee_id"),
            ("idx_tasks_creator", "tasks", "creator_id"),
            ("idx_tasks_state", "tasks", "state"),
            ("idx_tasks_created_at", "tasks", "created_at"),
            ("idx_tasks_message_id", "tasks", "message_id"),
            
            # Task Assignees indexes
            ("idx_task_assignees_ticket", "task_assignees", "ticket"),
            ("idx_task_assignees_assignee", "task_assignees", "assignee_id"),
            ("idx_task_assignees_status", "task_assignees", "status"),
            
            # Task Reactions indexes
            ("idx_task_reactions_ticket", "task_reactions", "ticket"),
            ("idx_task_reactions_message", "task_reactions", "message_id"),
            ("idx_task_reactions_user", "task_reactions", "user_id"),
            
            # QA Submissions indexes
            ("idx_qa_submissions_ticket", "qa_submissions", "ticket"),
            ("idx_qa_submissions_submitter", "qa_submissions", "submitter_id"),
            ("idx_qa_submissions_status", "qa_submissions", "status"),
            
            # QA Reviewers indexes
            ("idx_qa_reviewers_submission", "qa_reviewers", "qa_submission_id"),
            ("idx_qa_reviewers_reviewer", "qa_reviewers", "reviewer_id"),
            
            # QA Reactions indexes
            ("idx_qa_reactions_submission", "qa_reactions", "qa_submission_id"),
            ("idx_qa_reactions_user", "qa_reactions", "user_id"),
            
            # Issues indexes
            ("idx_issues_status", "issues", "status"),
            ("idx_issues_creator", "issues", "creator_id"),
            ("idx_issues_message", "issues", "message_id"),
            ("idx_issues_created_at", "issues", "created_at"),
            
            # Issue Handlers indexes
            ("idx_issue_handlers_issue", "issue_handlers", "issue_ticket"),
            ("idx_issue_handlers_handler", "issue_handlers", "handler_id"),
            
            # Issue Reactions indexes
            ("idx_issue_reactions_issue", "issue_reactions", "issue_ticket"),
            ("idx_issue_reactions_user", "issue_reactions", "user_id"),
            
            # Attendance indexes
            ("idx_attendance_user", "attendance", "user_id"),
            ("idx_attendance_date", "attendance", "date"),
            
            # Leave Requests indexes
            ("idx_leave_requests_user", "leave_requests", "user_id"),
            ("idx_leave_requests_status", "leave_requests", "status"),
            
            # Audit Trail indexes
            ("idx_audit_trail_ticket", "audit_trail", "ticket"),
            ("idx_audit_trail_user", "audit_trail", "user_id"),
            ("idx_audit_trail_timestamp", "audit_trail", "timestamp"),
            ("idx_audit_trail_event_type", "audit_trail", "event_type"),
            
            # Ticket Audit Trail indexes
            ("idx_ticket_audit_trail_ticket", "ticket_audit_trail", "ticket"),
            ("idx_ticket_audit_trail_action", "ticket_audit_trail", "action"),
            ("idx_ticket_audit_trail_changed_at", "ticket_audit_trail", "changed_at"),
            
            # Ticket Metadata indexes
            ("idx_ticket_metadata_ticket", "ticket_metadata", "ticket"),
            ("idx_ticket_metadata_key", "ticket_metadata", "key"),
            
            # Task Dependencies indexes
            ("idx_task_dependencies_ticket", "task_dependencies", "ticket"),
            ("idx_task_dependencies_blocked_by", "task_dependencies", "blocked_by_ticket"),
        ]
        
        for index_name, table, column in indexes:
            try:
                await self.conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})"
                )
            except Exception as e:
                logger.warning(f"Could not create index {index_name}: {e}")
    
    async def _run_migrations(self):
        """Run any pending database migrations."""
        # Check current schema version
        try:
            async with self.conn.execute(
                "SELECT MAX(version) as version FROM schema_migrations"
            ) as cursor:
                row = await cursor.fetchone()
                current_version = row['version'] if row and row['version'] else 0
        except:
            current_version = 0
        
        logger.info(f"Current schema version: {current_version}")
        
        # No additional migrations needed - all tables are in base schema now
        if current_version == 0:
            # Mark base schema as version 1
            await self.conn.execute("""
                INSERT INTO schema_migrations (version, name, applied_at)
                VALUES (1, 'base_schema', ?)
            """, (datetime.now().isoformat(),))
            await self.conn.commit()
            logger.info("Base schema initialized as version 1")
    
    # Task operations
    async def insert_task(self, task: Task):
        """Insert a new task."""
        try:
            await self.conn.execute("""
                INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.ticket, task.brand, task.assignee_id, task.creator_id,
                task.state.value, task.created_at.isoformat(),
                task.started_at.isoformat() if task.started_at else None,
                task.qa_submitted_at.isoformat() if task.qa_submitted_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                task.message_id, task.topic_id,
                1 if task.has_fire_exemption else 0,
                task.fire_exemption_by,
                task.fire_exemption_at.isoformat() if task.fire_exemption_at else None,
                task.deadline.isoformat() if task.deadline else None
            ))
            await self.conn.commit()
            logger.info(f"✅ Task inserted successfully: {task.ticket}")
        except Exception as e:
            logger.error(f"❌ Failed to insert task {task.ticket}: {e}", exc_info=True)
            raise
    
    async def get_task_by_ticket(self, ticket: str) -> Optional[Task]:
        """Get task by ticket ID."""
        # Ensure any pending writes are visible before querying
        # This is critical for duplicate detection
        await self.conn.commit()
        
        async with self.conn.execute(
            "SELECT * FROM tasks WHERE ticket = ?", (ticket,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Task.from_dict(dict(row))
            return None
    
    async def get_task_by_message_id(self, message_id: int) -> Optional[Task]:
        """Get task by message ID."""
        # Ensure any pending writes are visible before querying
        await self.conn.commit()
        
        async with self.conn.execute(
            "SELECT * FROM tasks WHERE message_id = ? LIMIT 1", (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Task.from_dict(dict(row))
            return None
    
    async def update_task_state(self, ticket: str, state: TaskState, timestamp: Optional[datetime] = None):
        """Update task state."""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Update appropriate timestamp field based on state
        if state == TaskState.STARTED:
            await self.conn.execute(
                "UPDATE tasks SET state = ?, started_at = ? WHERE ticket = ?",
                (state.value, timestamp.isoformat(), ticket)
            )
        elif state == TaskState.QA_SUBMITTED:
            await self.conn.execute(
                "UPDATE tasks SET state = ?, qa_submitted_at = ? WHERE ticket = ?",
                (state.value, timestamp.isoformat(), ticket)
            )
        elif state in (TaskState.APPROVED, TaskState.COMPLETED, TaskState.ARCHIVED):
            await self.conn.execute(
                "UPDATE tasks SET state = ?, completed_at = ? WHERE ticket = ?",
                (state.value, timestamp.isoformat(), ticket)
            )
        else:
            await self.conn.execute(
                "UPDATE tasks SET state = ? WHERE ticket = ?",
                (state.value, ticket)
            )
        
        await self.conn.commit()
    
    async def get_tasks_by_assignee(self, assignee_id: int, state: Optional[TaskState] = None) -> List[Task]:
        """Get tasks by assignee, excluding ARCHIVED tasks."""
        if state:
            query = "SELECT * FROM tasks WHERE assignee_id = ? AND state = ? AND state != ?"
            params = (assignee_id, state.value, TaskState.ARCHIVED.value)
        else:
            query = "SELECT * FROM tasks WHERE assignee_id = ? AND state != ?"
            params = (assignee_id, TaskState.ARCHIVED.value)
        
        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [Task.from_dict(dict(row)) for row in rows]
    
    async def get_tasks_by_state(self, state: TaskState) -> List[Task]:
        """Get all tasks in a specific state, excluding ARCHIVED tasks."""
        async with self.conn.execute(
            "SELECT * FROM tasks WHERE state = ? AND state != ?", 
            (state.value, TaskState.ARCHIVED.value)
        ) as cursor:
            rows = await cursor.fetchall()
            return [Task.from_dict(dict(row)) for row in rows]
    
    async def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        async with self.conn.execute("SELECT * FROM tasks") as cursor:
            rows = await cursor.fetchall()
            return [Task.from_dict(dict(row)) for row in rows]
    
    async def delete_task(self, ticket: str):
        """Delete a task from database."""
        import traceback
        logger.warning(f"⚠️ TASK DELETION REQUESTED: {ticket}")
        logger.warning(f"Stack trace:\n{''.join(traceback.format_stack())}")
        
        await self.conn.execute("DELETE FROM tasks WHERE ticket = ?", (ticket,))
        await self.conn.commit()
        logger.warning(f"❌ TASK DELETED: {ticket}")
    
    async def update_fire_exemption(self, ticket: str, user_id: Optional[int] = None, timestamp: Optional[datetime] = None):
        """Update fire exemption for a task."""
        if user_id is None:
            # Remove exemption
            await self.conn.execute("""
                UPDATE tasks 
                SET has_fire_exemption = 0, fire_exemption_by = NULL, fire_exemption_at = NULL
                WHERE ticket = ?
            """, (ticket,))
        else:
            # Add exemption
            if timestamp is None:
                timestamp = datetime.now()
            await self.conn.execute("""
                UPDATE tasks 
                SET has_fire_exemption = 1, fire_exemption_by = ?, fire_exemption_at = ?
                WHERE ticket = ?
            """, (user_id, timestamp.isoformat(), ticket))
        await self.conn.commit()
    
    async def update_task_message_id(self, ticket: str, new_message_id: int):
        """Update the message_id for a task (used when message is replaced)."""
        await self.conn.execute(
            "UPDATE tasks SET message_id = ? WHERE ticket = ?",
            (new_message_id, ticket)
        )
        await self.conn.commit()
        logger.info(f"✅ Updated message_id for task {ticket}: {new_message_id}")
    
    # Reaction operations
    async def insert_reaction(self, reaction: TaskReaction):
        """Insert a reaction."""
        await self.conn.execute("""
            INSERT INTO task_reactions (message_id, ticket, user_id, reaction, timestamp, topic_id, context, removed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reaction.message_id, reaction.ticket, reaction.user_id,
            reaction.reaction, reaction.timestamp.isoformat(), reaction.topic_id,
            None, None  # context and removed_at are optional
        ))
        await self.conn.commit()
    
    async def get_first_reaction(self, ticket: str, reaction_type: str) -> Optional[TaskReaction]:
        """Get the first reaction of a specific type for a task."""
        async with self.conn.execute("""
            SELECT * FROM task_reactions 
            WHERE ticket = ? AND reaction = ?
            ORDER BY timestamp ASC LIMIT 1
        """, (ticket, reaction_type)) as cursor:
            row = await cursor.fetchone()
            if row:
                return TaskReaction.from_dict(dict(row))
            return None
    
    async def get_reactions_by_ticket(self, ticket: str) -> List[TaskReaction]:
        """Get all reactions for a ticket."""
        async with self.conn.execute("""
            SELECT * FROM task_reactions 
            WHERE ticket = ?
            ORDER BY timestamp ASC
        """, (ticket,)) as cursor:
            rows = await cursor.fetchall()
            return [TaskReaction.from_dict(dict(row)) for row in rows]
    
    async def remove_reaction(self, ticket: str, user_id: int, reaction_type: str):
        """Remove a reaction from the database."""
        await self.conn.execute("""
            DELETE FROM task_reactions 
            WHERE ticket = ? AND user_id = ? AND reaction = ?
        """, (ticket, user_id, reaction_type))
        await self.conn.commit()
    
    # User operations
    async def insert_user(self, user: User):
        """Insert a new user."""
        await self.conn.execute("""
            INSERT OR REPLACE INTO users (
                user_id, username, first_name, last_name, full_name, email, phone,
                department, position, join_date, emergency_contact, blood_group,
                address, skills, notes, birth_date, birth_day, birth_month, birth_year,
                birthday_wishes_sent, custom_birthday_message, birthday_reminder_sent,
                role, created_at, last_active, is_on_leave, leave_start, leave_end,
                info_set_by, info_updated_at, info_complete
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.user_id, user.username, user.first_name, user.last_name,
            user.full_name, user.email, user.phone, user.department, user.position,
            user.join_date, user.emergency_contact, user.blood_group, user.address,
            user.skills, user.notes, user.birth_date, user.birth_day, user.birth_month,
            user.birth_year, user.birthday_wishes_sent, user.custom_birthday_message,
            user.birthday_reminder_sent,
            user.role.value if isinstance(user.role, UserRole) else user.role,
            user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
            user.last_active.isoformat() if user.last_active else datetime.now().isoformat(),
            1 if user.is_on_leave else 0,
            user.leave_start.isoformat() if user.leave_start else None,
            user.leave_end.isoformat() if user.leave_end else None,
            user.info_set_by, 
            user.info_updated_at.isoformat() if user.info_updated_at else None,
            1 if user.info_complete else 0
        ))
        await self.conn.commit()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        async with self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return User.from_dict(dict(row))
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username (case-insensitive)."""
        # Remove @ if present
        username = username.lstrip('@').lower()
        
        async with self.conn.execute(
            "SELECT * FROM users WHERE LOWER(username) = ?", (username,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return User.from_dict(dict(row))
            return None
    
    # QA operations
    async def insert_qa_submission(self, submission: QASubmission):
        """Insert a QA submission."""
        await self.conn.execute("""
            INSERT INTO qa_submissions (ticket, brand, asset, submitter_id, submitted_at, message_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            submission.ticket, submission.brand, submission.asset,
            submission.submitter_id, submission.submitted_at.isoformat(),
            submission.message_id, submission.status.value
        ))
        await self.conn.commit()
    
    async def get_qa_submission_by_ticket(self, ticket: str) -> Optional[QASubmission]:
        """Get QA submission by ticket."""
        async with self.conn.execute(
            "SELECT * FROM qa_submissions WHERE ticket = ? ORDER BY submitted_at DESC LIMIT 1",
            (ticket,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return QASubmission.from_dict(dict(row))
            return None
    
    async def get_qa_submission_by_message_id(self, message_id: int) -> Optional[QASubmission]:
        """Get QA submission by message ID."""
        async with self.conn.execute(
            "SELECT * FROM qa_submissions WHERE message_id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return QASubmission.from_dict(dict(row))
            return None
    
    async def update_qa_submission_status(
        self, ticket: str, status: QAStatus, reviewed_by: int, reviewed_at: datetime
    ):
        """Update QA submission status."""
        await self.conn.execute("""
            UPDATE qa_submissions 
            SET status = ?, reviewed_by = ?, reviewed_at = ?
            WHERE ticket = ?
        """, (status.value, reviewed_by, reviewed_at.isoformat(), ticket))
        await self.conn.commit()
    
    async def get_qa_submissions_by_status(self, status: QAStatus) -> List[QASubmission]:
        """Get QA submissions by status."""
        async with self.conn.execute(
            "SELECT * FROM qa_submissions WHERE status = ?", (status.value,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [QASubmission.from_dict(dict(row)) for row in rows]
    
    async def get_qa_submissions_by_submitter(self, submitter_id: int) -> List[QASubmission]:
        """Get QA submissions by submitter."""
        async with self.conn.execute(
            "SELECT * FROM qa_submissions WHERE submitter_id = ? ORDER BY submitted_at DESC",
            (submitter_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [QASubmission.from_dict(dict(row)) for row in rows]
    
    async def get_qa_submissions_older_than(self, hours: int) -> List[QASubmission]:
        """Get QA submissions older than specified hours."""
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        async with self.conn.execute(
            "SELECT * FROM qa_submissions WHERE submitted_at < ? AND status = ?",
            (cutoff_time.isoformat(), QAStatus.PENDING.value)
        ) as cursor:
            rows = await cursor.fetchall()
            return [QASubmission.from_dict(dict(row)) for row in rows]
    
    # Reject Feedback operations
    async def insert_reject_feedback(self, feedback: RejectFeedback):
        """Insert reject feedback."""
        await self.conn.execute("""
            INSERT INTO reject_feedback 
            (ticket, issue_type, problem, fix_required, assignee_id, reviewer_id, created_at, message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback.ticket, feedback.issue_type, feedback.problem,
            feedback.fix_required, feedback.assignee_id, feedback.reviewer_id,
            feedback.created_at.isoformat(), feedback.message_id
        ))
        await self.conn.commit()
    
    async def get_reject_feedback_by_ticket(self, ticket: str) -> Optional[RejectFeedback]:
        """Get reject feedback by ticket."""
        async with self.conn.execute(
            "SELECT * FROM reject_feedback WHERE ticket = ? ORDER BY created_at DESC LIMIT 1",
            (ticket,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return RejectFeedback.from_dict(dict(row))
            return None
    
    # Archive operations
    async def insert_archive(self, archive: Archive):
        """Insert an archive entry."""
        await self.conn.execute("""
            INSERT INTO archive 
            (ticket, assignee_id, qa_reviewer_id, archived_at, original_message_id, 
             qa_message_id, archive_message_id, completion_time_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            archive.ticket, archive.assignee_id, archive.qa_reviewer_id,
            archive.archived_at.isoformat(), archive.original_message_id,
            archive.qa_message_id, archive.archive_message_id,
            archive.completion_time_hours
        ))
        await self.conn.commit()
    
    async def get_archive_by_ticket(self, ticket: str) -> Optional[Archive]:
        """Get archive by ticket."""
        async with self.conn.execute(
            "SELECT * FROM archive WHERE ticket = ? ORDER BY archived_at DESC LIMIT 1",
            (ticket,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Archive.from_dict(dict(row))
            return None
    
    # Attendance operations
    async def insert_attendance(self, attendance: Attendance):
        """Insert an attendance record."""
        from src.data.models.attendance import Attendance
        await self.conn.execute("""
            INSERT INTO attendance 
            (user_id, date, checkin_time, checkout_time, is_late, is_auto_checkout, total_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            attendance.user_id,
            attendance.date.isoformat(),
            attendance.checkin_time.isoformat(),
            attendance.checkout_time.isoformat() if attendance.checkout_time else None,
            1 if attendance.is_late else 0,
            1 if attendance.is_auto_checkout else 0,
            attendance.total_hours
        ))
        await self.conn.commit()
    
    async def get_attendance_by_user_date(self, user_id: int, date) -> Optional[Attendance]:
        """Get attendance record for a user on a specific date."""
        from src.data.models.attendance import Attendance
        async with self.conn.execute(
            "SELECT * FROM attendance WHERE user_id = ? AND date = ?",
            (user_id, date.isoformat())
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Attendance.from_dict(dict(row))
            return None
    
    async def update_attendance_checkout(self, user_id: int, date, checkout_time, is_auto: bool):
        """Update checkout time for an attendance record."""
        from datetime import datetime as dt
        
        # Get the attendance record to calculate total hours
        attendance = await self.get_attendance_by_user_date(user_id, date)
        if not attendance:
            return
        
        # Calculate total hours
        total_seconds = (checkout_time - attendance.checkin_time).total_seconds()
        total_hours = total_seconds / 3600
        
        await self.conn.execute("""
            UPDATE attendance 
            SET checkout_time = ?, is_auto_checkout = ?, total_hours = ?
            WHERE user_id = ? AND date = ?
        """, (
            checkout_time.isoformat(),
            1 if is_auto else 0,
            total_hours,
            user_id,
            date.isoformat()
        ))
        await self.conn.commit()
    
    async def get_attendance_by_user_range(self, user_id: int, start_date, end_date):
        """Get attendance records for a user in a date range."""
        from src.data.models.attendance import Attendance
        async with self.conn.execute("""
            SELECT * FROM attendance 
            WHERE user_id = ? AND date >= ? AND date <= ?
            ORDER BY date DESC
        """, (user_id, start_date.isoformat(), end_date.isoformat())) as cursor:
            rows = await cursor.fetchall()
            return [Attendance.from_dict(dict(row)) for row in rows]
    
    async def get_late_checkins(self, user_id: int, start_date, end_date):
        """Get late check-ins for a user in a date range."""
        from src.data.models.attendance import Attendance
        async with self.conn.execute("""
            SELECT * FROM attendance 
            WHERE user_id = ? AND date >= ? AND date <= ? AND is_late = 1
            ORDER BY date DESC
        """, (user_id, start_date.isoformat(), end_date.isoformat())) as cursor:
            rows = await cursor.fetchall()
            return [Attendance.from_dict(dict(row)) for row in rows]
    
    # Break Record operations
    async def insert_break_record(self, break_record):
        """Insert a break record."""
        from src.data.models.break_record import BreakRecord
        await self.conn.execute("""
            INSERT INTO break_records 
            (user_id, date, break_start, break_end, reason, duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            break_record.user_id,
            break_record.date.isoformat(),
            break_record.break_start.isoformat(),
            break_record.break_end.isoformat() if break_record.break_end else None,
            break_record.reason,
            break_record.duration_minutes
        ))
        await self.conn.commit()
    
    async def get_active_break(self, user_id: int, date):
        """Get active break (not ended) for a user on a specific date."""
        from src.data.models.break_record import BreakRecord
        async with self.conn.execute("""
            SELECT * FROM break_records 
            WHERE user_id = ? AND date = ? AND break_end IS NULL
            ORDER BY break_start DESC LIMIT 1
        """, (user_id, date.isoformat())) as cursor:
            row = await cursor.fetchone()
            if row:
                return BreakRecord.from_dict(dict(row))
            return None
    
    async def update_break_end(self, break_id: int, break_end):
        """Update break end time and calculate duration."""
        # Get the break record to calculate duration
        from src.data.models.break_record import BreakRecord
        async with self.conn.execute(
            "SELECT * FROM break_records WHERE id = ?", (break_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return
            
            break_record = BreakRecord.from_dict(dict(row))
            
            # Calculate duration in minutes
            duration_seconds = (break_end - break_record.break_start).total_seconds()
            duration_minutes = duration_seconds / 60
        
        await self.conn.execute("""
            UPDATE break_records 
            SET break_end = ?, duration_minutes = ?
            WHERE id = ?
        """, (
            break_end.isoformat(),
            duration_minutes,
            break_id
        ))
        await self.conn.commit()
    
    async def get_breaks_by_user_date(self, user_id: int, date):
        """Get all breaks for a user on a specific date."""
        from src.data.models.break_record import BreakRecord
        async with self.conn.execute("""
            SELECT * FROM break_records 
            WHERE user_id = ? AND date = ?
            ORDER BY break_start ASC
        """, (user_id, date.isoformat())) as cursor:
            rows = await cursor.fetchall()
            return [BreakRecord.from_dict(dict(row)) for row in rows]
    
    async def get_breaks_by_user_range(self, user_id: int, start_date, end_date):
        """Get all breaks for a user in a date range."""
        from src.data.models.break_record import BreakRecord
        async with self.conn.execute("""
            SELECT * FROM break_records 
            WHERE user_id = ? AND date >= ? AND date <= ?
            ORDER BY date DESC, break_start ASC
        """, (user_id, start_date.isoformat(), end_date.isoformat())) as cursor:
            rows = await cursor.fetchall()
            return [BreakRecord.from_dict(dict(row)) for row in rows]
    
    # Leave Request operations
    async def insert_leave_request(self, leave_request):
        """Insert a leave request."""
        import json
        from src.data.models.leave_request import LeaveRequest
        await self.conn.execute("""
            INSERT INTO leave_requests 
            (user_id, start_date, end_date, reason, status, requested_at, message_id, reviewed_by, reviewed_at, replacement_user_id, task_handover_ids, is_notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            leave_request.user_id,
            leave_request.start_date.isoformat(),
            leave_request.end_date.isoformat(),
            leave_request.reason,
            leave_request.status.value,
            leave_request.requested_at.isoformat(),
            leave_request.message_id,
            leave_request.reviewed_by,
            leave_request.reviewed_at.isoformat() if leave_request.reviewed_at else None,
            leave_request.replacement_user_id,
            json.dumps(leave_request.task_handover_ids) if leave_request.task_handover_ids else None,
            1 if leave_request.is_notified else 0
        ))
        await self.conn.commit()
    
    async def get_leave_request_by_id(self, request_id: int):
        """Get leave request by ID."""
        from src.data.models.leave_request import LeaveRequest
        async with self.conn.execute(
            "SELECT * FROM leave_requests WHERE id = ?",
            (request_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return LeaveRequest.from_dict(dict(row))
            return None
    
    async def update_leave_request_status(self, request_id: int, status, reviewed_by: int, reviewed_at):
        """Update leave request status."""
        await self.conn.execute("""
            UPDATE leave_requests 
            SET status = ?, reviewed_by = ?, reviewed_at = ?
            WHERE id = ?
        """, (
            status.value,
            reviewed_by,
            reviewed_at.isoformat(),
            request_id
        ))
        await self.conn.commit()
    
    async def get_leave_requests_by_status(self, status):
        """Get leave requests by status."""
        from src.data.models.leave_request import LeaveRequest
        async with self.conn.execute(
            "SELECT * FROM leave_requests WHERE status = ? ORDER BY requested_at DESC",
            (status.value,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [LeaveRequest.from_dict(dict(row)) for row in rows]
    
    async def get_leave_requests_by_user(self, user_id: int):
        """Get leave requests for a user."""
        from src.data.models.leave_request import LeaveRequest
        async with self.conn.execute(
            "SELECT * FROM leave_requests WHERE user_id = ? ORDER BY requested_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [LeaveRequest.from_dict(dict(row)) for row in rows]
    
    # User operations
    async def update_user(self, user: User):
        """Update user information."""
        await self.insert_user(user)  # INSERT OR REPLACE handles updates
    
    async def update_user_last_active(self, user_id: int, timestamp: datetime):
        """Update user's last active timestamp."""
        await self.conn.execute(
            "UPDATE users SET last_active = ? WHERE user_id = ?",
            (timestamp.isoformat(), user_id)
        )
        await self.conn.commit()
    
    async def get_all_users(self) -> List[User]:
        """Get all users."""
        async with self.conn.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [User.from_dict(dict(row)) for row in rows]
    
    # Employee Information operations
    async def update_employee_info(self, user_id: int, info_dict: dict, set_by: str = "self"):
        """Update employee information for a user."""
        fields = []
        values = []
        
        # Map info_dict keys to database columns
        field_mapping = {
            "full_name": "full_name",
            "email": "email",
            "phone": "phone",
            "department": "department",
            "position": "position",
            "join_date": "join_date",
            "emergency_contact": "emergency_contact",
            "blood_group": "blood_group",
            "address": "address",
            "skills": "skills",
            "notes": "notes",
            "birth_date": "birth_date",
            "birth_day": "birth_day",
            "birth_month": "birth_month",
            "birth_year": "birth_year",
        }
        
        for key, db_column in field_mapping.items():
            if key in info_dict and info_dict[key] is not None:
                fields.append(f"{db_column} = ?")
                values.append(info_dict[key])
        
        # Add metadata
        fields.append("info_set_by = ?")
        values.append(set_by)
        fields.append("info_updated_at = ?")
        values.append(datetime.now().isoformat())
        
        # Check if info is complete (basic check - can be enhanced)
        if info_dict.get("full_name") and info_dict.get("email") and info_dict.get("phone"):
            fields.append("info_complete = ?")
            values.append(1)
        
        values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
        await self.conn.execute(query, tuple(values))
        await self.conn.commit()
    
    async def get_incomplete_profiles(self) -> List[User]:
        """Get users with incomplete employee information."""
        async with self.conn.execute(
            "SELECT * FROM users WHERE info_complete = 0 OR info_complete IS NULL"
        ) as cursor:
            rows = await cursor.fetchall()
            return [User.from_dict(dict(row)) for row in rows]
    
    # Birthday operations
    async def update_birthday(self, user_id: int, birth_date: str, birth_day: int,
                             birth_month: int, birth_year: Optional[int] = None):
        """Update user's birthday information."""
        await self.conn.execute("""
            UPDATE users 
            SET birth_date = ?, birth_day = ?, birth_month = ?, birth_year = ?
            WHERE user_id = ?
        """, (birth_date, birth_day, birth_month, birth_year, user_id))
        await self.conn.commit()
    
    async def get_users_with_birthday_today(self) -> List[User]:
        """Get all users with birthday today."""
        today = date.today()
        async with self.conn.execute("""
            SELECT * FROM users 
            WHERE birth_month = ? AND birth_day = ?
        """, (today.month, today.day)) as cursor:
            rows = await cursor.fetchall()
            return [User.from_dict(dict(row)) for row in rows]
    
    async def get_users_with_birthday_tomorrow(self) -> List[User]:
        """Get all users with birthday tomorrow."""
        from datetime import timedelta
        tomorrow = date.today() + timedelta(days=1)
        async with self.conn.execute("""
            SELECT * FROM users 
            WHERE birth_month = ? AND birth_day = ?
        """, (tomorrow.month, tomorrow.day)) as cursor:
            rows = await cursor.fetchall()
            return [User.from_dict(dict(row)) for row in rows]
    
    async def get_upcoming_birthdays(self, days: int = 30) -> List[User]:
        """Get users with birthdays in the next N days."""
        # This is a simplified version - for production, handle year boundaries
        today = date.today()
        users = []
        
        async with self.conn.execute("""
            SELECT * FROM users 
            WHERE birth_month IS NOT NULL AND birth_day IS NOT NULL
        """) as cursor:
            rows = await cursor.fetchall()
            all_users = [User.from_dict(dict(row)) for row in rows]
        
        for user in all_users:
            days_until = user.get_days_until_birthday()
            if days_until is not None and 0 <= days_until <= days:
                users.append(user)
        
        # Sort by days until birthday
        users.sort(key=lambda u: u.get_days_until_birthday() or 999)
        return users
    
    async def mark_birthday_wishes_sent(self, user_id: int, date_str: str):
        """Mark that birthday wishes were sent to user."""
        await self.conn.execute("""
            UPDATE users 
            SET birthday_wishes_sent = ?
            WHERE user_id = ?
        """, (date_str, user_id))
        await self.conn.commit()
    
    async def mark_birthday_reminder_sent(self, user_id: int, date_str: str):
        """Mark that birthday reminder was sent."""
        await self.conn.execute("""
            UPDATE users 
            SET birthday_reminder_sent = ?
            WHERE user_id = ?
        """, (date_str, user_id))
        await self.conn.commit()
    
    async def set_custom_birthday_message(self, user_id: int, message: str):
        """Set custom birthday message for user."""
        await self.conn.execute("""
            UPDATE users 
            SET custom_birthday_message = ?
            WHERE user_id = ?
        """, (message, user_id))
        await self.conn.commit()
    
    async def clear_custom_birthday_message(self, user_id: int):
        """Clear custom birthday message."""
        await self.conn.execute("""
            UPDATE users 
            SET custom_birthday_message = NULL
            WHERE user_id = ?
        """, (user_id,))
        await self.conn.commit()
    
    # Birthday wishes log operations
    async def log_birthday_wish(self, user_id: int, wish_date: str, wish_type: str,
                                custom_message: Optional[str] = None,
                                sent_by_user_id: Optional[int] = None,
                                dm_sent: bool = False, group_sent: bool = False):
        """Log a birthday wish in the database."""
        await self.conn.execute("""
            INSERT INTO birthday_wishes 
            (user_id, wish_date, wish_type, custom_message, sent_by_user_id, dm_sent, group_sent, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, wish_date, wish_type, custom_message, sent_by_user_id,
            1 if dm_sent else 0, 1 if group_sent else 0, datetime.now().isoformat()
        ))
        await self.conn.commit()
    
    async def log_birthday_reminder(self, user_id: int, reminder_date: str, birthday_date: str,
                                    user_dm_sent: bool = False, admin_dm_sent: bool = False,
                                    group_sent: bool = False):
        """Log a birthday reminder in the database."""
        await self.conn.execute("""
            INSERT INTO birthday_reminders 
            (user_id, reminder_date, birthday_date, user_dm_sent, admin_dm_sent, group_sent, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, reminder_date, birthday_date,
            1 if user_dm_sent else 0, 1 if admin_dm_sent else 0, 1 if group_sent else 0,
            datetime.now().isoformat()
        ))
        await self.conn.commit()
    
    async def get_birthday_wishes_for_user(self, user_id: int) -> List[dict]:
        """Get all birthday wishes sent to a user."""
        async with self.conn.execute("""
            SELECT * FROM birthday_wishes 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_birthday_reminders_for_user(self, user_id: int) -> List[dict]:
        """Get all birthday reminders sent for a user."""
        async with self.conn.execute("""
            SELECT * FROM birthday_reminders 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Additional task operations
    async def get_tasks_created_after(self, timestamp: datetime) -> List[Task]:
        """Get tasks created after a specific time."""
        async with self.conn.execute(
            "SELECT * FROM tasks WHERE created_at > ? AND state != ?", 
            (timestamp.isoformat(), TaskState.ARCHIVED.value)
        ) as cursor:
            rows = await cursor.fetchall()
            return [Task.from_dict(dict(row)) for row in rows]
    
    async def get_pending_tasks_without_fire(self, before_date: datetime) -> List[Task]:
        """Get pending tasks without fire exemption created before a date."""
        async with self.conn.execute("""
            SELECT * FROM tasks 
            WHERE created_at < ? 
            AND has_fire_exemption = 0 
            AND state IN (?, ?)
        """, (before_date.isoformat(), TaskState.ASSIGNED.value, TaskState.STARTED.value)) as cursor:
            rows = await cursor.fetchall()
            return [Task.from_dict(dict(row)) for row in rows]
    
    # Audit trail operations
    async def insert_audit_trail(self, audit: AuditTrail):
        """Insert an audit trail entry."""
        await self.conn.execute("""
            INSERT INTO audit_trail (event_type, timestamp, context, user_id, ticket, before_state, after_state, message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit.event_type.value, audit.timestamp.isoformat(),
            json.dumps(audit.context), audit.user_id, audit.ticket,
            audit.before_state, audit.after_state, audit.message_id
        ))
        await self.conn.commit()
    
    # Task dependency operations
    
    async def add_task_dependency(self, ticket: str, blocked_by_ticket: str, created_by: int):
        """Add a dependency - ticket is blocked by blocked_by_ticket."""
        try:
            await self.conn.execute("""
                INSERT INTO task_dependencies (ticket, blocked_by_ticket, created_at, created_by)
                VALUES (?, ?, ?, ?)
            """, (ticket, blocked_by_ticket, datetime.now().isoformat(), created_by))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding task dependency: {e}")
            return False
    
    async def remove_task_dependency(self, ticket: str, blocked_by_ticket: str):
        """Remove a dependency."""
        try:
            await self.conn.execute("""
                DELETE FROM task_dependencies 
                WHERE ticket = ? AND blocked_by_ticket = ?
            """, (ticket, blocked_by_ticket))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing task dependency: {e}")
            return False
    
    async def get_blocking_tasks(self, ticket: str) -> list:
        """Get all tasks that are blocking this ticket."""
        try:
            async with self.conn.execute("""
                SELECT blocked_by_ticket FROM task_dependencies 
                WHERE ticket = ?
            """, (ticket,)) as cursor:
                rows = await cursor.fetchall()
                return [row['blocked_by_ticket'] for row in rows]
        except Exception as e:
            logger.error(f"Error getting blocking tasks: {e}")
            return []
    
    async def get_blocked_tasks(self, ticket: str) -> list:
        """Get all tasks that are blocked by this ticket."""
        try:
            async with self.conn.execute("""
                SELECT ticket FROM task_dependencies 
                WHERE blocked_by_ticket = ?
            """, (ticket,)) as cursor:
                rows = await cursor.fetchall()
                return [row['ticket'] for row in rows]
        except Exception as e:
            logger.error(f"Error getting blocked tasks: {e}")
            return []
    
    async def has_blocking_tasks(self, ticket: str) -> bool:
        """Check if ticket has any blocking tasks."""
        blocking = await self.get_blocking_tasks(ticket)
        return len(blocking) > 0
    
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
    
    # Generic query methods for repositories
    async def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return cursor."""
        if params:
            cursor = await self.conn.execute(query, params)
        else:
            cursor = await self.conn.execute(query)
        await self.conn.commit()
        return cursor
    
    async def fetch_one(self, query: str, params: tuple = None):
        """Fetch one row from query."""
        if params:
            async with self.conn.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        else:
            async with self.conn.execute(query) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def fetch_all(self, query: str, params: tuple = None):
        """Fetch all rows from query."""
        if params:
            async with self.conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        else:
            async with self.conn.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]


    # ============================================================================
    # MEETING OPERATIONS
    # ============================================================================
    
    async def insert_meeting(self, meeting):
        """Insert a new meeting."""
        try:
            await self.conn.execute("""
                INSERT INTO meetings (
                    meeting_id, title, date, duration_minutes, location, organizer_id,
                    agenda, priority, status, created_at, message_id, topic_id,
                    preparation, notes_message_id, cancelled_reason, rescheduled_to,
                    reminded_24h_at, reminded_1h_at, reminded_15m_at, completed_at, cancelled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting.meeting_id,
                meeting.title,
                meeting.date.isoformat(),
                meeting.duration_minutes,
                meeting.location,
                meeting.organizer_id,
                meeting.agenda,
                meeting.priority.value,
                meeting.status.value,
                meeting.created_at.isoformat(),
                meeting.message_id,
                meeting.topic_id,
                meeting.preparation,
                meeting.notes_message_id,
                meeting.cancelled_reason,
                meeting.rescheduled_to,
                meeting.reminded_24h_at.isoformat() if meeting.reminded_24h_at else None,
                meeting.reminded_1h_at.isoformat() if meeting.reminded_1h_at else None,
                meeting.reminded_15m_at.isoformat() if meeting.reminded_15m_at else None,
                meeting.completed_at.isoformat() if meeting.completed_at else None,
                meeting.cancelled_at.isoformat() if meeting.cancelled_at else None,
            ))
            await self.conn.commit()
            logger.info(f"✅ Inserted meeting: {meeting.meeting_id}")
        except Exception as e:
            logger.error(f"❌ Error inserting meeting: {e}")
            raise
    
    async def get_meeting_by_id(self, meeting_id: str):
        """Get meeting by meeting ID."""
        await self.conn.commit()  # Ensure we see latest data
        async with self.conn.execute(
            "SELECT * FROM meetings WHERE meeting_id = ?", (meeting_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                from src.data.models import Meeting, MeetingStatus, MeetingPriority
                return Meeting(
                    meeting_id=row['meeting_id'],
                    title=row['title'],
                    date=datetime.fromisoformat(row['date']),
                    duration_minutes=row['duration_minutes'],
                    location=row['location'],
                    organizer_id=row['organizer_id'],
                    agenda=row['agenda'],
                    priority=MeetingPriority(row['priority']),
                    status=MeetingStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    message_id=row['message_id'],
                    topic_id=row['topic_id'],
                    preparation=row['preparation'],
                    notes_message_id=row['notes_message_id'],
                    cancelled_reason=row['cancelled_reason'],
                    rescheduled_to=row['rescheduled_to'],
                    reminded_24h_at=datetime.fromisoformat(row['reminded_24h_at']) if row['reminded_24h_at'] else None,
                    reminded_1h_at=datetime.fromisoformat(row['reminded_1h_at']) if row['reminded_1h_at'] else None,
                    reminded_15m_at=datetime.fromisoformat(row['reminded_15m_at']) if row['reminded_15m_at'] else None,
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                    cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
                )
            return None
    
    async def get_meeting_by_message_id(self, message_id: int):
        """Get meeting by message ID."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meetings WHERE message_id = ?", (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                from src.data.models import Meeting, MeetingStatus, MeetingPriority
                return Meeting(
                    meeting_id=row['meeting_id'],
                    title=row['title'],
                    date=datetime.fromisoformat(row['date']),
                    duration_minutes=row['duration_minutes'],
                    location=row['location'],
                    organizer_id=row['organizer_id'],
                    agenda=row['agenda'],
                    priority=MeetingPriority(row['priority']),
                    status=MeetingStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    message_id=row['message_id'],
                    topic_id=row['topic_id'],
                    preparation=row['preparation'],
                    notes_message_id=row['notes_message_id'],
                    cancelled_reason=row['cancelled_reason'],
                    rescheduled_to=row['rescheduled_to'],
                    reminded_24h_at=datetime.fromisoformat(row['reminded_24h_at']) if row['reminded_24h_at'] else None,
                    reminded_1h_at=datetime.fromisoformat(row['reminded_1h_at']) if row['reminded_1h_at'] else None,
                    reminded_15m_at=datetime.fromisoformat(row['reminded_15m_at']) if row['reminded_15m_at'] else None,
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                    cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
                )
            return None
    
    async def update_meeting_status(self, meeting_id: str, status, timestamp=None):
        """Update meeting status."""
        if timestamp is None:
            timestamp = datetime.now()
        
        status_field = None
        if status.value == 'COMPLETED':
            status_field = 'completed_at'
        elif status.value == 'CANCELLED':
            status_field = 'cancelled_at'
        
        if status_field:
            await self.conn.execute(f"""
                UPDATE meetings 
                SET status = ?, {status_field} = ?
                WHERE meeting_id = ?
            """, (status.value, timestamp.isoformat(), meeting_id))
        else:
            await self.conn.execute("""
                UPDATE meetings 
                SET status = ?
                WHERE meeting_id = ?
            """, (status.value, meeting_id))
        
        await self.conn.commit()
    
    async def update_meeting_reminder(self, meeting_id: str, reminder_type: str, timestamp):
        """Update meeting reminder timestamp."""
        field_map = {
            '24h': 'reminded_24h_at',
            '1h': 'reminded_1h_at',
            '15m': 'reminded_15m_at'
        }
        
        field = field_map.get(reminder_type)
        if not field:
            logger.error(f"Invalid reminder type: {reminder_type}")
            return
        
        await self.conn.execute(f"""
            UPDATE meetings 
            SET {field} = ?
            WHERE meeting_id = ?
        """, (timestamp.isoformat(), meeting_id))
        await self.conn.commit()
    
    async def update_meeting_notes_link(self, meeting_id: str, notes_message_id: int):
        """Link meeting notes message to meeting."""
        await self.conn.execute("""
            UPDATE meetings 
            SET notes_message_id = ?
            WHERE meeting_id = ?
        """, (notes_message_id, meeting_id))
        await self.conn.commit()
    
    async def cancel_meeting(self, meeting_id: str, reason: str, cancelled_at):
        """Cancel a meeting."""
        from src.data.models import MeetingStatus
        await self.conn.execute("""
            UPDATE meetings 
            SET status = ?, cancelled_reason = ?, cancelled_at = ?
            WHERE meeting_id = ?
        """, (MeetingStatus.CANCELLED.value, reason, cancelled_at.isoformat(), meeting_id))
        await self.conn.commit()
    
    async def reschedule_meeting(self, meeting_id: str, new_meeting_id: str):
        """Mark meeting as rescheduled."""
        from src.data.models import MeetingStatus
        await self.conn.execute("""
            UPDATE meetings 
            SET status = ?, rescheduled_to = ?
            WHERE meeting_id = ?
        """, (MeetingStatus.RESCHEDULED.value, new_meeting_id, meeting_id))
        await self.conn.commit()
    
    async def get_meetings_after_date(self, after_date):
        """Get all meetings after a specific date."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meetings WHERE date > ? ORDER BY date ASC",
            (after_date.isoformat(),)
        ) as cursor:
            rows = await cursor.fetchall()
            from src.data.models import Meeting, MeetingStatus, MeetingPriority
            return [
                Meeting(
                    meeting_id=row['meeting_id'],
                    title=row['title'],
                    date=datetime.fromisoformat(row['date']),
                    duration_minutes=row['duration_minutes'],
                    location=row['location'],
                    organizer_id=row['organizer_id'],
                    agenda=row['agenda'],
                    priority=MeetingPriority(row['priority']),
                    status=MeetingStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    message_id=row['message_id'],
                    topic_id=row['topic_id'],
                    preparation=row['preparation'],
                    notes_message_id=row['notes_message_id'],
                    cancelled_reason=row['cancelled_reason'],
                    rescheduled_to=row['rescheduled_to'],
                    reminded_24h_at=datetime.fromisoformat(row['reminded_24h_at']) if row['reminded_24h_at'] else None,
                    reminded_1h_at=datetime.fromisoformat(row['reminded_1h_at']) if row['reminded_1h_at'] else None,
                    reminded_15m_at=datetime.fromisoformat(row['reminded_15m_at']) if row['reminded_15m_at'] else None,
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                    cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
                )
                for row in rows
            ]
    
    async def get_meetings_by_organizer(self, organizer_id: int):
        """Get all meetings organized by a user."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meetings WHERE organizer_id = ? ORDER BY date DESC",
            (organizer_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            from src.data.models import Meeting, MeetingStatus, MeetingPriority
            return [
                Meeting(
                    meeting_id=row['meeting_id'],
                    title=row['title'],
                    date=datetime.fromisoformat(row['date']),
                    duration_minutes=row['duration_minutes'],
                    location=row['location'],
                    organizer_id=row['organizer_id'],
                    agenda=row['agenda'],
                    priority=MeetingPriority(row['priority']),
                    status=MeetingStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    message_id=row['message_id'],
                    topic_id=row['topic_id'],
                    preparation=row['preparation'],
                    notes_message_id=row['notes_message_id'],
                    cancelled_reason=row['cancelled_reason'],
                    rescheduled_to=row['rescheduled_to'],
                    reminded_24h_at=datetime.fromisoformat(row['reminded_24h_at']) if row['reminded_24h_at'] else None,
                    reminded_1h_at=datetime.fromisoformat(row['reminded_1h_at']) if row['reminded_1h_at'] else None,
                    reminded_15m_at=datetime.fromisoformat(row['reminded_15m_at']) if row['reminded_15m_at'] else None,
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                    cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
                )
                for row in rows
            ]
    
    async def get_meetings_by_status(self, status):
        """Get all meetings with a specific status."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meetings WHERE status = ? ORDER BY date ASC",
            (status.value,)
        ) as cursor:
            rows = await cursor.fetchall()
            from src.data.models import Meeting, MeetingStatus, MeetingPriority
            return [
                Meeting(
                    meeting_id=row['meeting_id'],
                    title=row['title'],
                    date=datetime.fromisoformat(row['date']),
                    duration_minutes=row['duration_minutes'],
                    location=row['location'],
                    organizer_id=row['organizer_id'],
                    agenda=row['agenda'],
                    priority=MeetingPriority(row['priority']),
                    status=MeetingStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    message_id=row['message_id'],
                    topic_id=row['topic_id'],
                    preparation=row['preparation'],
                    notes_message_id=row['notes_message_id'],
                    cancelled_reason=row['cancelled_reason'],
                    rescheduled_to=row['rescheduled_to'],
                    reminded_24h_at=datetime.fromisoformat(row['reminded_24h_at']) if row['reminded_24h_at'] else None,
                    reminded_1h_at=datetime.fromisoformat(row['reminded_1h_at']) if row['reminded_1h_at'] else None,
                    reminded_15m_at=datetime.fromisoformat(row['reminded_15m_at']) if row['reminded_15m_at'] else None,
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                    cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
                )
                for row in rows
            ]
    
    async def get_meetings_needing_reminders(self, reminder_type: str, current_time):
        """Get meetings that need reminders sent."""
        field_map = {
            '24h': 'reminded_24h_at',
            '1h': 'reminded_1h_at',
            '15m': 'reminded_15m_at'
        }
        
        field = field_map.get(reminder_type)
        if not field:
            return []
        
        # Calculate time window based on reminder type
        from datetime import timedelta
        if reminder_type == '24h':
            window_start = current_time + timedelta(hours=23, minutes=50)
            window_end = current_time + timedelta(hours=24, minutes=10)
        elif reminder_type == '1h':
            window_start = current_time + timedelta(minutes=50)
            window_end = current_time + timedelta(minutes=70)
        else:  # 15m
            window_start = current_time + timedelta(minutes=10)
            window_end = current_time + timedelta(minutes=20)
        
        await self.conn.commit()
        async with self.conn.execute(f"""
            SELECT * FROM meetings 
            WHERE status = 'SCHEDULED' 
            AND {field} IS NULL
            AND date BETWEEN ? AND ?
            ORDER BY date ASC
        """, (window_start.isoformat(), window_end.isoformat())) as cursor:
            rows = await cursor.fetchall()
            from src.data.models import Meeting, MeetingStatus, MeetingPriority
            return [
                Meeting(
                    meeting_id=row['meeting_id'],
                    title=row['title'],
                    date=datetime.fromisoformat(row['date']),
                    duration_minutes=row['duration_minutes'],
                    location=row['location'],
                    organizer_id=row['organizer_id'],
                    agenda=row['agenda'],
                    priority=MeetingPriority(row['priority']),
                    status=MeetingStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    message_id=row['message_id'],
                    topic_id=row['topic_id'],
                    preparation=row['preparation'],
                    notes_message_id=row['notes_message_id'],
                    cancelled_reason=row['cancelled_reason'],
                    rescheduled_to=row['rescheduled_to'],
                    reminded_24h_at=datetime.fromisoformat(row['reminded_24h_at']) if row['reminded_24h_at'] else None,
                    reminded_1h_at=datetime.fromisoformat(row['reminded_1h_at']) if row['reminded_1h_at'] else None,
                    reminded_15m_at=datetime.fromisoformat(row['reminded_15m_at']) if row['reminded_15m_at'] else None,
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                    cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
                )
                for row in rows
            ]
    
    # ============================================================================
    # MEETING ATTENDEE OPERATIONS
    # ============================================================================
    
    async def insert_meeting_attendee(self, attendee):
        """Insert a meeting attendee."""
        try:
            await self.conn.execute("""
                INSERT INTO meeting_attendees (
                    meeting_id, user_id, status, invited_at, responded_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                attendee.meeting_id,
                attendee.user_id,
                attendee.status.value,
                attendee.invited_at.isoformat(),
                attendee.responded_at.isoformat() if attendee.responded_at else None,
            ))
            await self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Error inserting meeting attendee: {e}")
            raise
    
    async def update_attendee_status(self, meeting_id: str, user_id: int, status, responded_at):
        """Update attendee RSVP status."""
        await self.conn.execute("""
            UPDATE meeting_attendees 
            SET status = ?, responded_at = ?
            WHERE meeting_id = ? AND user_id = ?
        """, (status.value, responded_at.isoformat(), meeting_id, user_id))
        await self.conn.commit()
    
    async def get_meeting_attendees(self, meeting_id: str):
        """Get all attendees for a meeting."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meeting_attendees WHERE meeting_id = ?",
            (meeting_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            from src.data.models import MeetingAttendee, AttendanceStatus
            return [
                MeetingAttendee(
                    id=row['id'],
                    meeting_id=row['meeting_id'],
                    user_id=row['user_id'],
                    status=AttendanceStatus(row['status']),
                    invited_at=datetime.fromisoformat(row['invited_at']),
                    responded_at=datetime.fromisoformat(row['responded_at']) if row['responded_at'] else None,
                )
                for row in rows
            ]
    
    async def get_meeting_attendee(self, meeting_id: str, user_id: int):
        """Get specific attendee record."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meeting_attendees WHERE meeting_id = ? AND user_id = ?",
            (meeting_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                from src.data.models import MeetingAttendee, AttendanceStatus
                return MeetingAttendee(
                    id=row['id'],
                    meeting_id=row['meeting_id'],
                    user_id=row['user_id'],
                    status=AttendanceStatus(row['status']),
                    invited_at=datetime.fromisoformat(row['invited_at']),
                    responded_at=datetime.fromisoformat(row['responded_at']) if row['responded_at'] else None,
                )
            return None
    
    async def get_user_meetings(self, user_id: int, after_date=None):
        """Get all meetings a user is invited to."""
        await self.conn.commit()
        if after_date:
            async with self.conn.execute("""
                SELECT m.* FROM meetings m
                JOIN meeting_attendees ma ON m.meeting_id = ma.meeting_id
                WHERE ma.user_id = ? AND m.date > ?
                ORDER BY m.date ASC
            """, (user_id, after_date.isoformat())) as cursor:
                rows = await cursor.fetchall()
        else:
            async with self.conn.execute("""
                SELECT m.* FROM meetings m
                JOIN meeting_attendees ma ON m.meeting_id = ma.meeting_id
                WHERE ma.user_id = ?
                ORDER BY m.date DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
        
        from src.data.models import Meeting, MeetingStatus, MeetingPriority
        return [
            Meeting(
                meeting_id=row['meeting_id'],
                title=row['title'],
                date=datetime.fromisoformat(row['date']),
                duration_minutes=row['duration_minutes'],
                location=row['location'],
                organizer_id=row['organizer_id'],
                agenda=row['agenda'],
                priority=MeetingPriority(row['priority']),
                status=MeetingStatus(row['status']),
                created_at=datetime.fromisoformat(row['created_at']),
                message_id=row['message_id'],
                topic_id=row['topic_id'],
                preparation=row['preparation'],
                notes_message_id=row['notes_message_id'],
                cancelled_reason=row['cancelled_reason'],
                rescheduled_to=row['rescheduled_to'],
                reminded_24h_at=datetime.fromisoformat(row['reminded_24h_at']) if row['reminded_24h_at'] else None,
                reminded_1h_at=datetime.fromisoformat(row['reminded_1h_at']) if row['reminded_1h_at'] else None,
                reminded_15m_at=datetime.fromisoformat(row['reminded_15m_at']) if row['reminded_15m_at'] else None,
                completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                cancelled_at=datetime.fromisoformat(row['cancelled_at']) if row['cancelled_at'] else None,
            )
            for row in rows
        ]
    
    # ============================================================================
    # MEETING NOTES OPERATIONS
    # ============================================================================
    
    async def insert_meeting_notes(self, notes):
        """Insert meeting notes."""
        try:
            await self.conn.execute("""
                INSERT INTO meeting_notes (
                    meeting_id, posted_by, posted_at, message_id,
                    attendees_present, decisions, action_items, next_meeting_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notes.meeting_id,
                notes.posted_by,
                notes.posted_at.isoformat(),
                notes.message_id,
                notes.attendees_present,
                notes.decisions,
                notes.action_items,
                notes.next_meeting_date.isoformat() if notes.next_meeting_date else None,
            ))
            await self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Error inserting meeting notes: {e}")
            raise
    
    async def get_meeting_notes_by_meeting_id(self, meeting_id: str):
        """Get meeting notes by meeting ID."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meeting_notes WHERE meeting_id = ?",
            (meeting_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                from src.data.models import MeetingNotes
                return MeetingNotes(
                    id=row['id'],
                    meeting_id=row['meeting_id'],
                    posted_by=row['posted_by'],
                    posted_at=datetime.fromisoformat(row['posted_at']),
                    message_id=row['message_id'],
                    attendees_present=row['attendees_present'],
                    decisions=row['decisions'],
                    action_items=row['action_items'],
                    next_meeting_date=datetime.fromisoformat(row['next_meeting_date']) if row['next_meeting_date'] else None,
                )
            return None
    
    async def get_meeting_notes_by_message_id(self, message_id: int):
        """Get meeting notes by message ID."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meeting_notes WHERE message_id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                from src.data.models import MeetingNotes
                return MeetingNotes(
                    id=row['id'],
                    meeting_id=row['meeting_id'],
                    posted_by=row['posted_by'],
                    posted_at=datetime.fromisoformat(row['posted_at']),
                    message_id=row['message_id'],
                    attendees_present=row['attendees_present'],
                    decisions=row['decisions'],
                    action_items=row['action_items'],
                    next_meeting_date=datetime.fromisoformat(row['next_meeting_date']) if row['next_meeting_date'] else None,
                )
            return None
    
    # ============================================================================
    # MEETING REACTION OPERATIONS
    # ============================================================================
    
    async def insert_meeting_reaction(self, reaction):
        """Insert a meeting reaction (RSVP)."""
        try:
            await self.conn.execute("""
                INSERT OR REPLACE INTO meeting_reactions (
                    meeting_id, message_id, user_id, reaction, timestamp
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                reaction.meeting_id,
                reaction.message_id,
                reaction.user_id,
                reaction.reaction,
                reaction.timestamp.isoformat(),
            ))
            await self.conn.commit()
        except Exception as e:
            logger.error(f"❌ Error inserting meeting reaction: {e}")
            raise
    
    async def remove_meeting_reaction(self, meeting_id: str, user_id: int, reaction: str):
        """Remove a meeting reaction."""
        await self.conn.execute("""
            DELETE FROM meeting_reactions 
            WHERE meeting_id = ? AND user_id = ? AND reaction = ?
        """, (meeting_id, user_id, reaction))
        await self.conn.commit()
    
    async def get_meeting_reactions(self, meeting_id: str):
        """Get all reactions for a meeting."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meeting_reactions WHERE meeting_id = ? ORDER BY timestamp ASC",
            (meeting_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            from src.data.models import MeetingReaction
            return [
                MeetingReaction(
                    id=row['id'],
                    meeting_id=row['meeting_id'],
                    message_id=row['message_id'],
                    user_id=row['user_id'],
                    reaction=row['reaction'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                )
                for row in rows
            ]
    
    async def get_user_meeting_reactions(self, meeting_id: str, user_id: int):
        """Get user's reactions for a meeting."""
        await self.conn.commit()
        async with self.conn.execute(
            "SELECT * FROM meeting_reactions WHERE meeting_id = ? AND user_id = ? ORDER BY timestamp DESC",
            (meeting_id, user_id)
        ) as cursor:
            rows = await cursor.fetchall()
            from src.data.models import MeetingReaction
            return [
                MeetingReaction(
                    id=row['id'],
                    meeting_id=row['meeting_id'],
                    message_id=row['message_id'],
                    user_id=row['user_id'],
                    reaction=row['reaction'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                )
                for row in rows
            ]
