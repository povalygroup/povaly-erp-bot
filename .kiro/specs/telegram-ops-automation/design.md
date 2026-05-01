# Design Document: Telegram Operations Automation System

## Overview

The Telegram Operations Automation System is an enterprise-grade bot that manages task workflows, QA reviews, attendance tracking, and automated reporting for Povaly Group. The system leverages Telegram's native reaction mechanism as a state engine, enabling seamless team coordination across multiple logical topic channels within a single Telegram group.

### Key Design Principles

1. **Modularity**: Clean separation of concerns with independent, testable components
2. **Scalability**: Support for 50-500 concurrent users and 1000+ daily operations
3. **Portability**: Environment-based configuration enabling easy deployment to any server
4. **Maintainability**: Well-organized code structure with clear interfaces and documentation
5. **Reliability**: Robust error handling, retry mechanisms, and comprehensive audit trails
6. **Flexibility**: Database abstraction supporting SQLite, MongoDB, and JSON storage

### System Capabilities

- **Task Management**: Creation, assignment, tracking, and archival of work items
- **QA Workflow**: Structured submission, review, approval/rejection with feedback
- **Attendance Tracking**: Automated check-in/check-out with late detection
- **Leave Management**: Request submission and approval workflow
- **Automated Reporting**: Daily sync reports and weekly performance analytics
- **Inactivity Detection**: Progressive escalation system for stalled tasks
- **Violation Detection**: Automated enforcement of format and workflow rules
- **Smart Notifications**: Context-aware routing to appropriate channels
- **Performance Monitoring**: Real-time metrics and predictive alerts
- **Role-Based Access Control**: Granular permissions across all topics

## Architecture

### High-Level Architecture

The system follows a layered architecture with clear separation between presentation, business logic, and data access layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Bot API                         │
│                  (External Interface)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Bot Application Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Message Handler (Webhook/Polling)                     │ │
│  └────────────┬───────────────────────────────────────────┘ │
│               │                                              │
│  ┌────────────▼───────────────────────────────────────────┐ │
│  │  Topic Router                                          │ │
│  │  (Routes messages to appropriate handlers)             │ │
│  └────────────┬───────────────────────────────────────────┘ │
└───────────────┼──────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────┐
│                  Business Logic Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Message    │  │   Reaction   │  │    State     │       │
│  │    Parser    │  │   Tracker    │  │   Engine     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Violation   │  │ Notification │  │  Scheduler   │       │
│  │  Detection   │  │   Router     │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Performance  │  │    Report    │  │   Access     │       │
│  │  Monitor     │  │  Generator   │  │   Control    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└───────────────┬──────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────┐
│                  Service Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    Task      │  │      QA      │  │  Attendance  │       │
│  │   Service    │  │   Service    │  │   Service    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    Leave     │  │    Report    │  │    User      │       │
│  │   Service    │  │   Service    │  │   Service    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└───────────────┬──────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────┐
│              Data Access Layer (Repository Pattern)           │
│  ┌──────────────────────────────────────────────────────────┐│
│  │         Database Abstraction Interface                   ││
│  └────────┬─────────────────┬─────────────────┬─────────────┘│
│           │                 │                 │               │
│  ┌────────▼────┐   ┌────────▼────┐   ┌────────▼────┐        │
│  │   SQLite    │   │   MongoDB   │   │    JSON     │        │
│  │  Adapter    │   │   Adapter   │   │   Adapter   │        │
│  └─────────────┘   └─────────────┘   └─────────────┘        │
└───────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

**Task Creation Flow:**
```
User posts message → Message Handler → Topic Router → Message Parser
→ Task Service → Database → State Engine → Notification Router → User
```

**Reaction-Based State Transition Flow:**
```
User adds reaction → Reaction Tracker → State Engine → Task Service
→ Database → Notification Router → User/Admin Control Panel
```

**Scheduled Report Generation Flow:**
```
Scheduler triggers → Report Generator → Task/QA/Attendance Services
→ Database queries → Report formatting → Notification Router → Daily Sync topic
```

### Technology Stack

**Core Framework:**
- **Python 3.11+**: Modern async/await support, type hints, performance improvements
- **python-telegram-bot v20+**: Async-first Telegram Bot API wrapper with webhook support
- **APScheduler 3.x**: Advanced task scheduling with cron-like capabilities

**Database Layer:**
- **SQLite3**: Default lightweight embedded database for single-server deployments
- **PyMongo**: MongoDB driver for distributed deployments
- **JSON**: File-based storage for development and testing

**Supporting Libraries:**
- **python-dotenv**: Environment variable management
- **pytz**: Timezone handling (GMT+6 support)
- **asyncio**: Asynchronous I/O for concurrent operations
- **aiofiles**: Async file operations for JSON storage
- **cryptography**: Data encryption for sensitive information

**Development & Deployment:**
- **Docker**: Containerization for consistent deployments
- **Docker Compose**: Multi-container orchestration
- **pytest**: Testing framework with async support
- **black**: Code formatting
- **mypy**: Static type checking

## Components and Interfaces

### 1. Message Handler

**Responsibility**: Receives and processes incoming Telegram messages and reactions

**Interface:**
```python
class MessageHandler:
    async def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Process incoming message"""
        
    async def handle_reaction(self, update: Update, context: CallbackContext) -> None:
        """Process reaction additions"""
        
    async def handle_callback_query(self, update: Update, context: CallbackContext) -> None:
        """Process inline button callbacks"""
```

**Key Operations:**
- Extract message metadata (user_id, message_id, topic_id, timestamp)
- Route to appropriate topic handler
- Handle errors and retry failed operations
- Log all incoming events to audit trail

### 2. Topic Router

**Responsibility**: Routes messages to appropriate handlers based on topic ID

**Interface:**
```python
class TopicRouter:
    def __init__(self, config: Config):
        self.topic_handlers = {
            config.TOPIC_TASK_ALLOCATION: TaskAllocationHandler(),
            config.TOPIC_QA_REVIEW: QAReviewHandler(),
            config.TOPIC_ATTENDANCE_LEAVE: AttendanceHandler(),
            config.TOPIC_ADMIN_CONTROL_PANEL: AdminHandler(),
            # ... other topics
        }
    
    async def route(self, message: Message) -> None:
        """Route message to appropriate handler"""
```

**Key Operations:**
- Match message topic_id to configured topics
- Delegate to specialized handlers
- Apply topic-specific permission checks
- Log routing decisions

### 3. Message Parser

**Responsibility**: Extracts structured data from message text

**Interface:**
```python
class MessageParser:
    def parse_task_message(self, text: str) -> Optional[TaskData]:
        """Extract TICKET and assignee from task message"""
        
    def parse_qa_submission(self, text: str) -> Optional[QASubmissionData]:
        """Extract [TICKET][BRAND][ASSET] from QA message"""
        
    def parse_reject_feedback(self, text: str) -> Optional[RejectFeedbackData]:
        """Extract [TICKET][ISSUE_TYPE][PROBLEM][FIX_REQUIRED][ASSIGNEE]"""
        
    def parse_leave_request(self, text: str) -> Optional[LeaveRequestData]:
        """Extract start_date, end_date, reason from leave request"""
        
    def extract_mentions(self, text: str) -> List[str]:
        """Extract @username mentions"""
```

**Key Operations:**
- Regex-based pattern matching for structured formats
- Whitespace normalization
- Validation of extracted fields
- Error reporting for malformed messages

### 4. Reaction Tracker

**Responsibility**: Monitors and records reaction events

**Interface:**
```python
class ReactionTracker:
    async def track_reaction(self, message_id: int, user_id: int, 
                            reaction: str, timestamp: datetime) -> None:
        """Record reaction event"""
        
    async def get_first_reaction(self, message_id: int, 
                                 reaction_type: str) -> Optional[ReactionEvent]:
        """Get first occurrence of reaction type"""
        
    async def validate_reactor_permission(self, user_id: int, 
                                         reaction: str, topic_id: int) -> bool:
        """Check if user can add this reaction in this topic"""
```

**Key Operations:**
- Store reaction events with timestamps
- Track only 👍 reactions in Task Allocation topic
- Track ❤️ and 👎 reactions in QA & Review topic
- Validate user permissions before processing
- Ignore reaction removals

### 5. State Engine

**Responsibility**: Manages task state transitions based on events

**Interface:**
```python
class StateEngine:
    async def transition(self, ticket: str, event: StateEvent) -> StateTransition:
        """Execute state transition"""
        
    def validate_transition(self, current_state: TaskState, 
                           event: StateEvent) -> bool:
        """Check if transition is valid"""
        
    async def get_current_state(self, ticket: str) -> TaskState:
        """Get current task state"""
```

**State Machine:**
```
ASSIGNED → (👍 reaction) → STARTED
STARTED → (QA submission) → QA_SUBMITTED
QA_SUBMITTED → (❤️ reaction) → APPROVED
QA_SUBMITTED → (👎 reaction) → REJECTED
APPROVED → (archival) → ARCHIVED
REJECTED → (new QA submission) → QA_SUBMITTED
ASSIGNED → (inactivity timeout) → INACTIVE
INACTIVE → (👍 reaction) → STARTED
```

**Key Operations:**
- Validate state transitions
- Record transition history
- Trigger side effects (notifications, archival)
- Handle concurrent transitions

### 6. Violation Detection Engine

**Responsibility**: Identifies and handles rule violations

**Interface:**
```python
class ViolationDetectionEngine:
    async def check_format_violation(self, message: Message, 
                                     expected_format: str) -> Optional[Violation]:
        """Check message format compliance"""
        
    async def check_workflow_violation(self, user_id: int, 
                                      action: str, context: dict) -> Optional[Violation]:
        """Check workflow rule compliance"""
        
    async def check_permission_violation(self, user_id: int, 
                                        action: str, topic_id: int) -> Optional[Violation]:
        """Check permission compliance"""
        
    async def handle_violation(self, violation: Violation) -> None:
        """Execute violation handling logic"""
```

**Violation Types:**
- **Format Violations**: Malformed QA submissions, incorrect ticket format
- **Workflow Violations**: QA submission for unassigned task, duplicate task creation
- **Permission Violations**: Unauthorized reactions, restricted topic access
- **Attendance Violations**: Late check-in, missing check-out
- **Performance Violations**: Excessive inactivity, high rejection rate

**Key Operations:**
- Detect violations in real-time
- Apply auto-remediation when configured
- Send direct messages with correction guidance
- Escalate repeated violations
- Log all violations to audit trail

### 7. Notification Router

**Responsibility**: Routes notifications to appropriate channels

**Interface:**
```python
class NotificationRouter:
    async def send_direct_message(self, user_id: int, message: str, 
                                  link: Optional[str] = None) -> None:
        """Send DM to user"""
        
    async def send_topic_message(self, topic_id: int, message: str) -> None:
        """Post message to topic"""
        
    async def batch_notifications(self, user_id: int, 
                                  notifications: List[Notification]) -> None:
        """Batch multiple notifications"""
        
    def should_send_dm(self, notification_type: str) -> bool:
        """Check if DM should be sent based on config"""
```

**Routing Rules:**
- **Direct Messages**: Task assignments, rejections, inactivity warnings, leave status, format violations
- **Daily Sync Topic**: Daily reports, weekly reports
- **Admin Control Panel**: Escalations, security alerts, performance flags, repeated violations
- **Work Topics**: Never receive bot notification spam

**Key Operations:**
- Route based on notification type and audience
- Batch notifications within 5-minute windows
- Prioritize critical over informational
- Include message links when configured
- Respect user notification preferences

### 8. Scheduler

**Responsibility**: Triggers time-based operations

**Interface:**
```python
class Scheduler:
    def schedule_daily_report(self, time: str, timezone: str) -> None:
        """Schedule daily sync report generation"""
        
    def schedule_weekly_report(self, day: str, time: str, timezone: str) -> None:
        """Schedule weekly performance report"""
        
    def schedule_daily_summary(self, time: str, timezone: str) -> None:
        """Schedule daily summary messages"""
        
    def schedule_inactivity_check(self, interval_hours: int) -> None:
        """Schedule periodic inactivity checks"""
        
    def schedule_database_backup(self, time: str, timezone: str) -> None:
        """Schedule daily database backup"""
```

**Scheduled Jobs:**
- **Daily Summary Messages**: 00:00 GMT+6 (Task Allocation & QA Review topics)
- **Daily Sync Reports**: 22:30 GMT+6 (per-user task progress)
- **Weekly Reports**: Sunday 22:30 GMT+6 (performance analytics)
- **Inactivity Checks**: Every hour
- **Database Backups**: 23:00 GMT+6
- **Auto Check-out**: 23:59 GMT+6

**Key Operations:**
- Use APScheduler with cron triggers
- Handle timezone conversions (GMT+6)
- Retry failed jobs with exponential backoff
- Log all scheduled executions
- Support dynamic job addition/removal

### 9. Report Generator

**Responsibility**: Generates formatted reports

**Interface:**
```python
class ReportGenerator:
    async def generate_daily_sync(self, user_id: int, date: datetime) -> str:
        """Generate daily sync report for user"""
        
    async def generate_weekly_report(self, start_date: datetime, 
                                    end_date: datetime) -> str:
        """Generate weekly performance report"""
        
    async def generate_daily_summary(self, date: datetime, 
                                     topic: str) -> List[str]:
        """Generate daily summary messages"""
        
    async def generate_qa_daily_summary(self, date: datetime) -> List[str]:
        """Generate QA daily summary messages"""
```

**Report Formats:**

**Daily Sync Report:**
```
📊 Daily Sync Report - [User Name]
📅 Date: [Month DD, YYYY]

🔗 Task Summary: [link to daily summary]
🔗 QA Summary: [link to QA daily summary]
📌 Starting Ticket: [TICKET-ID]

✅ COMPLETED (X tasks)
• [TICKET] - [time ago]
...

🚀 STARTED (X tasks)
• [TICKET] - [time ago]
...

⏸️ NOT TOUCHED (X tasks)
• [TICKET] - [time ago]
...

❌ REJECTED (X tasks)
• [TICKET] - [ISSUE_TYPE] - [time ago]
  Feedback: [truncated feedback]
...

📈 Summary: X total tasks | Y completed | Z rejected
```

**Weekly Report:**
```
📊 Weekly Performance Report
📅 Week: [Month DD - DD, YYYY]

🏆 TOP PERFORMERS
1. [User] - XX% completion rate
2. [User] - XX% completion rate
...

⚠️ PERFORMANCE ALERTS
• [User] - XX% completion rate (below 50%)
• [User] - XX% QA rejection rate (above threshold)
...

📊 TEAM METRICS
• Total tasks completed: XXX
• Average completion time: X.X hours
• QA approval rate: XX%
• Average pending tasks/day: XX
• Average rejected tasks/day: XX

📈 TRENDS
• Completion rate: [improving/stable/declining]
• QA quality: [improving/stable/declining]
```

**Key Operations:**
- Query database for relevant data
- Format with emojis and structure
- Include clickable message links
- Calculate metrics and trends
- Group by assignee/reviewer

### 10. Performance Monitor

**Responsibility**: Tracks metrics and generates alerts

**Interface:**
```python
class PerformanceMonitor:
    async def calculate_qa_rejection_rate(self, user_id: int, 
                                         period_days: int) -> float:
        """Calculate QA rejection rate"""
        
    async def calculate_task_dormancy(self, user_id: int) -> int:
        """Calculate days since last completion"""
        
    async def calculate_late_checkin_count(self, user_id: int, 
                                          period_days: int) -> int:
        """Count late check-ins"""
        
    async def check_qa_bottlenecks(self) -> List[BottleneckAlert]:
        """Identify tasks stuck in QA"""
        
    async def generate_performance_alert(self, alert: PerformanceAlert) -> None:
        """Send alert to Admin Control Panel"""
```

**Monitored Metrics:**
- QA rejection rate per user
- Task dormancy (days without completion)
- Late check-in frequency
- Average task completion time
- QA bottlenecks (>48 hours in review)
- Team-wide completion trends

**Key Operations:**
- Calculate metrics in real-time
- Compare against configured thresholds
- Generate alerts for Admin Control Panel
- Store historical metrics
- Support trend analysis

## Data Models

### Database Schema

The system uses a unified schema that works across SQLite, MongoDB, and JSON storage through the repository pattern.

**Users Table:**
```python
{
    "user_id": int,              # Telegram user ID (primary key)
    "username": str,             # Telegram username
    "full_name": str,            # Display name
    "role": str,                 # "regular", "qa_reviewer", "manager", "admin", "owner"
    "created_at": datetime,
    "last_active": datetime,
    "is_on_leave": bool,
    "leave_start": datetime,     # Nullable
    "leave_end": datetime        # Nullable
}
```

**Tasks Table:**
```python
{
    "ticket": str,               # Primary key (e.g., "PV-2404-1")
    "brand": str,                # Brand code
    "assignee_id": int,          # Foreign key to Users
    "creator_id": int,           # Foreign key to Users
    "state": str,                # "ASSIGNED", "STARTED", "QA_SUBMITTED", "APPROVED", "REJECTED", "ARCHIVED", "INACTIVE"
    "created_at": datetime,
    "started_at": datetime,      # Nullable (first 👍 reaction)
    "qa_submitted_at": datetime, # Nullable
    "completed_at": datetime,    # Nullable (approved or archived)
    "message_id": int,           # Original message ID in Task Allocation
    "topic_id": int,             # Topic where task was created
    "has_fire_exemption": bool,  # 🔥 reaction from authorized user
    "fire_exemption_by": int,    # User ID who added 🔥
    "fire_exemption_at": datetime # Nullable
}
```

**Task_Reactions Table:**
```python
{
    "id": int,                   # Auto-increment primary key
    "message_id": int,           # Foreign key
    "ticket": str,               # Foreign key to Tasks
    "user_id": int,              # Foreign key to Users
    "reaction": str,             # "👍", "❤️", "👎", "🔥"
    "timestamp": datetime,
    "topic_id": int
}
```

**QA_Submissions Table:**
```python
{
    "id": int,                   # Auto-increment primary key
    "ticket": str,               # Foreign key to Tasks
    "brand": str,
    "asset": str,                # Asset description
    "submitter_id": int,         # Foreign key to Users
    "submitted_at": datetime,
    "message_id": int,           # QA submission message ID
    "status": str,               # "PENDING", "APPROVED", "REJECTED"
    "reviewed_by": int,          # Nullable, foreign key to Users
    "reviewed_at": datetime      # Nullable
}
```

**Reject_Feedback Table:**
```python
{
    "id": int,                   # Auto-increment primary key
    "ticket": str,               # Foreign key to Tasks
    "issue_type": str,
    "problem": str,
    "fix_required": str,
    "assignee_id": int,          # Foreign key to Users
    "reviewer_id": int,          # Foreign key to Users
    "created_at": datetime,
    "message_id": int
}
```

**Leave_Requests Table:**
```python
{
    "id": int,                   # Auto-increment primary key
    "user_id": int,              # Foreign key to Users
    "start_date": date,
    "end_date": date,
    "reason": str,               # Encrypted
    "status": str,               # "PENDING", "APPROVED", "REJECTED"
    "requested_at": datetime,
    "reviewed_by": int,          # Nullable, foreign key to Users
    "reviewed_at": datetime,     # Nullable
    "message_id": int
}
```

**Attendance Table:**
```python
{
    "id": int,                   # Auto-increment primary key
    "user_id": int,              # Foreign key to Users
    "date": date,
    "checkin_time": datetime,
    "checkout_time": datetime,   # Nullable
    "is_late": bool,
    "is_auto_checkout": bool,
    "total_hours": float         # Nullable
}
```

**Archive Table:**
```python
{
    "id": int,                   # Auto-increment primary key
    "ticket": str,               # Foreign key to Tasks
    "assignee_id": int,          # Foreign key to Users
    "qa_reviewer_id": int,       # Foreign key to Users
    "archived_at": datetime,
    "original_message_id": int,
    "qa_message_id": int,
    "archive_message_id": int,   # Message ID in Central Archive topic
    "completion_time_hours": float
}
```

**Reports Table:**
```python
{
    "id": int,                   # Auto-increment primary key
    "report_type": str,          # "DAILY_SYNC", "WEEKLY", "DAILY_SUMMARY", "QA_DAILY_SUMMARY"
    "user_id": int,              # Nullable (null for team-wide reports)
    "date": date,
    "content": str,              # Full report text
    "message_id": int,           # Message ID where report was posted
    "generated_at": datetime,
    "metrics": dict              # JSON field with calculated metrics
}
```

**Violations Table:**
```python
{
    "id": int,                   # Auto-increment primary key
    "user_id": int,              # Foreign key to Users
    "violation_type": str,       # "FORMAT", "WORKFLOW", "PERMISSION", "ATTENDANCE", "PERFORMANCE"
    "description": str,
    "context": dict,             # JSON field with violation details
    "detected_at": datetime,
    "action_taken": str,         # "AUTO_DELETE", "WARNING_SENT", "ESCALATED", "LOGGED"
    "message_id": int            # Nullable
}
```

**Audit_Trail Table:**
```python
{
    "id": int,                   # Auto-increment primary key
    "event_type": str,           # "STATE_TRANSITION", "REACTION", "QA_SUBMISSION", "VIOLATION", etc.
    "user_id": int,              # Nullable
    "ticket": str,               # Nullable
    "before_state": str,         # Nullable
    "after_state": str,          # Nullable
    "context": dict,             # JSON field with full event context
    "timestamp": datetime,
    "message_id": int            # Nullable
}
```

### Indexes for Performance

**SQLite/MongoDB Indexes:**
```sql
-- Tasks
CREATE INDEX idx_tasks_assignee ON Tasks(assignee_id);
CREATE INDEX idx_tasks_state ON Tasks(state);
CREATE INDEX idx_tasks_created_at ON Tasks(created_at);

-- Task_Reactions
CREATE INDEX idx_reactions_message ON Task_Reactions(message_id);
CREATE INDEX idx_reactions_ticket ON Task_Reactions(ticket);
CREATE INDEX idx_reactions_timestamp ON Task_Reactions(timestamp);

-- QA_Submissions
CREATE INDEX idx_qa_ticket ON QA_Submissions(ticket);
CREATE INDEX idx_qa_status ON QA_Submissions(status);
CREATE INDEX idx_qa_submitted_at ON QA_Submissions(submitted_at);

-- Attendance
CREATE INDEX idx_attendance_user_date ON Attendance(user_id, date);

-- Audit_Trail
CREATE INDEX idx_audit_user ON Audit_Trail(user_id);
CREATE INDEX idx_audit_ticket ON Audit_Trail(ticket);
CREATE INDEX idx_audit_timestamp ON Audit_Trail(timestamp);
CREATE INDEX idx_audit_event_type ON Audit_Trail(event_type);
```

### Database Abstraction Layer

**Repository Interface:**
```python
class DatabaseRepository(ABC):
    @abstractmethod
    async def create_task(self, task: Task) -> None:
        pass
    
    @abstractmethod
    async def get_task(self, ticket: str) -> Optional[Task]:
        pass
    
    @abstractmethod
    async def update_task_state(self, ticket: str, state: str) -> None:
        pass
    
    @abstractmethod
    async def get_tasks_by_assignee(self, user_id: int, 
                                    state: Optional[str] = None) -> List[Task]:
        pass
    
    # ... similar methods for all entities
```

**Concrete Implementations:**
```python
class SQLiteRepository(DatabaseRepository):
    """SQLite implementation using aiosqlite"""
    
class MongoDBRepository(DatabaseRepository):
    """MongoDB implementation using motor (async PyMongo)"""
    
class JSONRepository(DatabaseRepository):
    """JSON file-based implementation using aiofiles"""
```

**Factory Pattern:**
```python
class RepositoryFactory:
    @staticmethod
    def create(db_type: str, config: dict) -> DatabaseRepository:
        if db_type == "sqlite":
            return SQLiteRepository(config["path"])
        elif db_type == "mongodb":
            return MongoDBRepository(config["uri"], config["database"])
        elif db_type == "json":
            return JSONRepository(config["path"])
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
```


## Project Structure

The system follows a clean, modular structure optimized for maintainability and scalability:

```
telegram-ops-automation/
├── .env                          # Environment configuration (not in git)
├── .env.template                 # Configuration template with documentation
├── .gitignore
├── README.md
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Multi-container orchestration
├── setup.py                      # Package installation
│
├── src/                          # Source code
│   ├── __init__.py
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Configuration management
│   │
│   ├── bot/                      # Bot application layer
│   │   ├── __init__.py
│   │   ├── application.py        # Bot application setup
│   │   ├── handlers/             # Message and reaction handlers
│   │   │   ├── __init__.py
│   │   │   ├── message_handler.py
│   │   │   ├── reaction_handler.py
│   │   │   ├── callback_handler.py
│   │   │   └── command_handler.py
│   │   └── routers/              # Topic-based routing
│   │       ├── __init__.py
│   │       ├── topic_router.py
│   │       ├── task_allocation_handler.py
│   │       ├── qa_review_handler.py
│   │       ├── attendance_handler.py
│   │       └── admin_handler.py
│   │
│   ├── core/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── parser/               # Message parsing
│   │   │   ├── __init__.py
│   │   │   ├── message_parser.py
│   │   │   ├── task_parser.py
│   │   │   ├── qa_parser.py
│   │   │   └── leave_parser.py
│   │   ├── state/                # State management
│   │   │   ├── __init__.py
│   │   │   ├── state_engine.py
│   │   │   ├── state_machine.py
│   │   │   └── reaction_tracker.py
│   │   ├── violation/            # Violation detection
│   │   │   ├── __init__.py
│   │   │   ├── detection_engine.py
│   │   │   ├── format_validator.py
│   │   │   ├── workflow_validator.py
│   │   │   └── permission_validator.py
│   │   ├── notification/         # Notification routing
│   │   │   ├── __init__.py
│   │   │   ├── notification_router.py
│   │   │   ├── message_formatter.py
│   │   │   └── batch_manager.py
│   │   ├── scheduler/            # Task scheduling
│   │   │   ├── __init__.py
│   │   │   ├── scheduler.py
│   │   │   ├── jobs.py
│   │   │   └── cron_config.py
│   │   ├── monitoring/           # Performance monitoring
│   │   │   ├── __init__.py
│   │   │   ├── performance_monitor.py
│   │   │   ├── metrics_calculator.py
│   │   │   └── alert_generator.py
│   │   └── reporting/            # Report generation
│   │       ├── __init__.py
│   │       ├── report_generator.py
│   │       ├── daily_sync.py
│   │       ├── weekly_report.py
│   │       ├── daily_summary.py
│   │       └── qa_summary.py
│   │
│   ├── services/                 # Service layer
│   │   ├── __init__.py
│   │   ├── task_service.py
│   │   ├── qa_service.py
│   │   ├── attendance_service.py
│   │   ├── leave_service.py
│   │   ├── report_service.py
│   │   ├── user_service.py
│   │   └── archive_service.py
│   │
│   ├── data/                     # Data access layer
│   │   ├── __init__.py
│   │   ├── models/               # Data models
│   │   │   ├── __init__.py
│   │   │   ├── task.py
│   │   │   ├── user.py
│   │   │   ├── qa_submission.py
│   │   │   ├── attendance.py
│   │   │   ├── leave_request.py
│   │   │   ├── report.py
│   │   │   └── violation.py
│   │   ├── repositories/         # Repository pattern
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py
│   │   │   ├── task_repository.py
│   │   │   ├── user_repository.py
│   │   │   ├── qa_repository.py
│   │   │   ├── attendance_repository.py
│   │   │   └── audit_repository.py
│   │   └── adapters/             # Database adapters
│   │       ├── __init__.py
│   │       ├── sqlite_adapter.py
│   │       ├── mongodb_adapter.py
│   │       ├── json_adapter.py
│   │       └── factory.py
│   │
│   ├── security/                 # Security and access control
│   │   ├── __init__.py
│   │   ├── access_control.py
│   │   ├── permission_matrix.py
│   │   ├── encryption.py
│   │   └── audit_logger.py
│   │
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── time_utils.py
│       ├── format_utils.py
│       ├── link_builder.py
│       └── validators.py
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── unit/                     # Unit tests
│   │   ├── test_parser.py
│   │   ├── test_state_engine.py
│   │   ├── test_violation_detection.py
│   │   └── ...
│   ├── integration/              # Integration tests
│   │   ├── test_task_workflow.py
│   │   ├── test_qa_workflow.py
│   │   └── ...
│   └── fixtures/                 # Test fixtures
│       ├── sample_messages.py
│       └── mock_data.py
│
├── scripts/                      # Utility scripts
│   ├── setup_database.py         # Database initialization
│   ├── migrate_database.py       # Migration tool
│   ├── backup_database.py        # Backup utility
│   └── restore_database.py       # Restore utility
│
├── data/                         # Data directory (created at runtime)
│   ├── povaly_bot.db             # SQLite database (if using SQLite)
│   ├── backups/                  # Database backups
│   └── logs/                     # Application logs
│
└── docs/                         # Documentation
    ├── setup.md                  # Setup instructions
    ├── deployment.md             # Deployment guide
    ├── configuration.md          # Configuration reference
    ├── architecture.md           # Architecture documentation
    └── api.md                    # API documentation
```

### Key Design Decisions

**1. Layered Architecture:**
- Clear separation between bot handlers, business logic, services, and data access
- Each layer has well-defined responsibilities and interfaces
- Easy to test and maintain

**2. Repository Pattern:**
- Abstracts database operations behind a common interface
- Enables switching between SQLite, MongoDB, and JSON without code changes
- Simplifies testing with mock repositories

**3. Service Layer:**
- Encapsulates business logic for each domain (tasks, QA, attendance)
- Provides clean API for handlers and schedulers
- Handles transactions and cross-cutting concerns

**4. Modular Components:**
- Each component (parser, state engine, notification router) is independent
- Components communicate through well-defined interfaces
- Easy to extend and modify

**5. Configuration-Driven:**
- All settings in .env file
- No hardcoded values in source code
- Easy to deploy to different environments

## Error Handling

### Error Handling Strategy

The system implements a comprehensive error handling strategy with multiple layers:

**1. Message Processing Errors:**
```python
async def handle_message(self, update: Update, context: CallbackContext) -> None:
    try:
        # Process message
        await self.process_message(update.message)
    except ParsingError as e:
        # Log parsing error and notify user
        logger.error(f"Parsing error: {e}", extra={"message_id": update.message.message_id})
        await self.send_format_correction(update.message.from_user.id, e.expected_format)
    except DatabaseError as e:
        # Retry database operation
        logger.error(f"Database error: {e}", extra={"message_id": update.message.message_id})
        await self.retry_with_backoff(self.process_message, update.message)
    except Exception as e:
        # Log unexpected error and continue
        logger.exception(f"Unexpected error: {e}", extra={"message_id": update.message.message_id})
        await self.notify_admin(f"Critical error processing message: {e}")
```

**2. Database Operation Errors:**
```python
async def execute_with_retry(self, operation: Callable, max_retries: int = 5) -> Any:
    """Execute database operation with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return await operation()
        except DatabaseConnectionError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            logger.warning(f"Database connection failed, retrying in {wait_time}s")
            await asyncio.sleep(wait_time)
```

**3. Scheduled Job Errors:**
```python
async def execute_scheduled_job(self, job_func: Callable) -> None:
    """Execute scheduled job with error handling"""
    try:
        await job_func()
    except Exception as e:
        logger.exception(f"Scheduled job failed: {job_func.__name__}")
        await self.notify_admin(f"Scheduled job failed: {job_func.__name__}: {e}")
        # Job will retry on next schedule
```

**4. Notification Errors:**
```python
async def send_notification(self, user_id: int, message: str) -> bool:
    """Send notification with error handling"""
    try:
        await self.bot.send_message(user_id, message)
        return True
    except TelegramError as e:
        if e.message == "Forbidden: bot was blocked by the user":
            logger.info(f"User {user_id} has blocked the bot")
            await self.mark_user_notifications_disabled(user_id)
        else:
            logger.error(f"Failed to send notification to {user_id}: {e}")
        return False
```

### Error Categories and Handling

| Error Category | Handling Strategy | User Notification | Admin Alert |
|---------------|-------------------|-------------------|-------------|
| Parsing Errors | Log + Send format template | Yes (DM) | No |
| Database Errors | Retry with backoff | No | Yes (if all retries fail) |
| Permission Violations | Log to audit trail | Yes (DM) | Yes (if repeated) |
| Workflow Violations | Log + Auto-remediate | Yes (DM) | No |
| Telegram API Errors | Retry + Log | No | Yes (if critical) |
| Scheduled Job Failures | Log + Retry next cycle | No | Yes |
| Configuration Errors | Exit with error message | N/A | N/A |

### Logging Strategy

**Log Levels:**
- **DEBUG**: Detailed flow information for development
- **INFO**: Normal operations (task created, state transition, report generated)
- **WARNING**: Recoverable issues (retry attempts, user blocked bot)
- **ERROR**: Operation failures (database errors, API errors)
- **CRITICAL**: System-level failures (configuration errors, startup failures)

**Log Format:**
```python
{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "level": "INFO",
    "logger": "task_service",
    "message": "Task created successfully",
    "context": {
        "ticket": "PV-2404-1",
        "assignee_id": 123456,
        "creator_id": 789012,
        "message_id": 456789
    }
}
```

**Log Rotation:**
- Daily rotation at midnight GMT+6
- Retention: 30 days (configurable via LOG_RETENTION_DAYS)
- Compression of archived logs
- Separate log files for different components

## Testing Strategy

### Testing Approach

The system uses a dual testing approach combining unit tests and integration tests:

**Unit Tests:**
- Test individual components in isolation
- Mock external dependencies (database, Telegram API)
- Fast execution (<1 second per test)
- High coverage of business logic

**Integration Tests:**
- Test component interactions
- Use test database (SQLite in-memory)
- Test complete workflows end-to-end
- Verify state transitions and side effects

### Test Coverage Goals

- **Overall Coverage**: >80%
- **Business Logic**: >90%
- **Data Access Layer**: >85%
- **Handlers**: >75%

### Unit Test Examples

**Message Parser Tests:**
```python
def test_parse_qa_submission_valid():
    parser = MessageParser()
    text = "[PV-2404-1][PV][Video thumbnail]"
    result = parser.parse_qa_submission(text)
    
    assert result is not None
    assert result.ticket == "PV-2404-1"
    assert result.brand == "PV"
    assert result.asset == "Video thumbnail"

def test_parse_qa_submission_invalid():
    parser = MessageParser()
    text = "[PV-2404-1] Missing brackets"
    result = parser.parse_qa_submission(text)
    
    assert result is None
```

**State Engine Tests:**
```python
@pytest.mark.asyncio
async def test_state_transition_assigned_to_started():
    engine = StateEngine(mock_repository)
    
    # Setup
    await mock_repository.create_task(Task(
        ticket="PV-2404-1",
        state="ASSIGNED",
        assignee_id=123
    ))
    
    # Execute
    event = StateEvent(type="REACTION", reaction="👍", user_id=123)
    transition = await engine.transition("PV-2404-1", event)
    
    # Verify
    assert transition.from_state == "ASSIGNED"
    assert transition.to_state == "STARTED"
    assert transition.success is True
```

**Violation Detection Tests:**
```python
@pytest.mark.asyncio
async def test_detect_format_violation():
    detector = ViolationDetectionEngine(config)
    message = Message(text="[PV-2404-1] Missing format", from_user=User(id=123))
    
    violation = await detector.check_format_violation(message, "QA_SUBMISSION")
    
    assert violation is not None
    assert violation.type == "FORMAT"
    assert violation.user_id == 123
```

### Integration Test Examples

**Task Workflow Integration Test:**
```python
@pytest.mark.asyncio
async def test_complete_task_workflow():
    # Setup
    bot = create_test_bot()
    db = create_test_database()
    
    # 1. Create task
    task_message = create_message("[PV-2404-1] @user1 Create video")
    await bot.handle_message(task_message)
    task = await db.get_task("PV-2404-1")
    assert task.state == "ASSIGNED"
    
    # 2. Start task (👍 reaction)
    reaction_update = create_reaction_update(task_message.message_id, "👍", user1_id)
    await bot.handle_reaction(reaction_update)
    task = await db.get_task("PV-2404-1")
    assert task.state == "STARTED"
    
    # 3. Submit QA
    qa_message = create_message("[PV-2404-1][PV][Video]")
    await bot.handle_message(qa_message)
    task = await db.get_task("PV-2404-1")
    assert task.state == "QA_SUBMITTED"
    
    # 4. Approve QA (❤️ reaction)
    qa_reaction = create_reaction_update(qa_message.message_id, "❤️", qa_reviewer_id)
    await bot.handle_reaction(qa_reaction)
    task = await db.get_task("PV-2404-1")
    assert task.state == "APPROVED"
    
    # 5. Verify archival
    archive = await db.get_archive_by_ticket("PV-2404-1")
    assert archive is not None
    assert task.state == "ARCHIVED"
```

### Test Configuration

**pytest.ini:**
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
```

**Test Fixtures:**
```python
@pytest.fixture
async def test_database():
    """Create in-memory SQLite database for testing"""
    db = SQLiteRepository(":memory:")
    await db.initialize()
    yield db
    await db.close()

@pytest.fixture
def mock_bot():
    """Create mock Telegram bot"""
    bot = AsyncMock(spec=Bot)
    return bot

@pytest.fixture
def config():
    """Create test configuration"""
    return Config(
        TELEGRAM_BOT_TOKEN="test_token",
        DATABASE_TYPE="sqlite",
        DATABASE_PATH=":memory:",
        # ... other test config
    )
```

## Deployment Strategy

### Containerization with Docker

**Dockerfile:**
```dockerfile
# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 botuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=botuser:botuser src/ ./src/
COPY --chown=botuser:botuser scripts/ ./scripts/

# Create data directory
RUN mkdir -p /app/data/logs /app/data/backups && \
    chown -R botuser:botuser /app/data

# Switch to non-root user
USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run application
CMD ["python", "-m", "src.main"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  telegram-bot:
    build: .
    container_name: povaly-telegram-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/data/logs
    networks:
      - bot-network
    depends_on:
      - mongodb
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  mongodb:
    image: mongo:7.0
    container_name: povaly-mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: povaly_bot
    volumes:
      - mongodb-data:/data/db
      - ./backups:/backups
    networks:
      - bot-network
    ports:
      - "27017:27017"

networks:
  bot-network:
    driver: bridge

volumes:
  mongodb-data:
```

### Deployment Options

**Option 1: Docker Compose (Recommended for single-server)**
```bash
# Clone repository
git clone <repository-url>
cd telegram-ops-automation

# Copy and configure environment
cp .env.template .env
nano .env  # Edit configuration

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f telegram-bot

# Stop
docker-compose down
```

**Option 2: Standalone Docker**
```bash
# Build image
docker build -t telegram-ops-bot:latest .

# Run container
docker run -d \
  --name povaly-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  telegram-ops-bot:latest

# View logs
docker logs -f povaly-bot
```

**Option 3: systemd Service (Direct Python)**
```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/telegram-bot.service
```

```ini
[Unit]
Description=Telegram Operations Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/telegram-ops-automation
Environment="PATH=/opt/telegram-ops-automation/venv/bin"
EnvironmentFile=/opt/telegram-ops-automation/.env
ExecStart=/opt/telegram-ops-automation/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

**Option 4: PM2 (Node.js Process Manager)**
```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'telegram-bot',
    script: 'venv/bin/python',
    args: '-m src.main',
    cwd: '/opt/telegram-ops-automation',
    interpreter: 'none',
    env_file: '.env',
    autorestart: true,
    watch: false,
    max_memory_restart: '500M'
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

**Option 5: Cloud Deployment (AWS ECS, Google Cloud Run, Azure Container Instances)**

*AWS ECS Example:*
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t telegram-ops-bot .
docker tag telegram-ops-bot:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/telegram-ops-bot:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/telegram-ops-bot:latest

# Create ECS task definition and service
aws ecs create-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster telegram-bot-cluster --service-name telegram-bot --task-definition telegram-bot:1
```

### Database Migration and Backup

**Database Initialization:**
```bash
# Run setup script
python scripts/setup_database.py

# Or use Docker
docker-compose exec telegram-bot python scripts/setup_database.py
```

**Database Migration:**
```bash
# Migrate from SQLite to MongoDB
python scripts/migrate_database.py \
  --source sqlite \
  --source-path ./data/povaly_bot.db \
  --target mongodb \
  --target-uri mongodb://localhost:27017/povaly_bot

# Migrate from JSON to SQLite
python scripts/migrate_database.py \
  --source json \
  --source-path ./data/json_storage \
  --target sqlite \
  --target-path ./data/povaly_bot.db
```

**Backup and Restore:**
```bash
# Manual backup
python scripts/backup_database.py --output ./backups/backup-$(date +%Y%m%d).db

# Restore from backup
python scripts/restore_database.py --input ./backups/backup-20240115.db

# Automated backups (configured in .env)
# DATABASE_BACKUP_TIME=23:00
# Backups run automatically at 23:00 GMT+6 daily
```

### Environment Configuration

**.env.template** (comprehensive example):
```bash
# ============================================
# Bot Configuration
# ============================================
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_GROUP_ID=-1001234567890

# ============================================
# Database Configuration
# ============================================
# Options: sqlite, mongodb, json
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/povaly_bot.db
DATABASE_BACKUP_TIME=23:00

# MongoDB Configuration (if using mongodb)
# MONGO_URI=mongodb://username:password@localhost:27017/
# MONGO_DATABASE=povaly_bot

# ============================================
# Timezone
# ============================================
TIMEZONE=GMT+6

# ============================================
# Topic IDs (Telegram Thread IDs)
# ============================================
TOPIC_OFFICIAL_DIRECTIVES=2
TOPIC_BRAND_REPOSITORY=3
TOPIC_TASK_ALLOCATION=4
TOPIC_CORE_OPERATIONS=5
TOPIC_QA_REVIEW=6
TOPIC_CENTRAL_ARCHIVE=7
TOPIC_DAILY_SYNC=8
TOPIC_ATTENDANCE_LEAVE=9
TOPIC_ADMIN_CONTROL_PANEL=10
TOPIC_STRATEGIC_LOUNGE=11

# ============================================
# User Roles (Comma-separated Telegram User IDs)
# ============================================
ADMINISTRATORS=123456789,987654321
MANAGERS=111222333,444555666
QA_REVIEWERS=777888999,123123123
OWNERS=123456789

# ============================================
# Inactivity Thresholds (Hours)
# ============================================
INACTIVITY_WARNING_HOURS=18
INACTIVITY_MARK_HOURS=24
INACTIVITY_ESCALATE_HOURS=48
INACTIVITY_CRITICAL_HOURS=72

# ============================================
# Attendance Configuration (HH:MM format GMT+6)
# ============================================
ATTENDANCE_LATE_CHECKIN_TIME=11:00
ATTENDANCE_AUTO_CHECKOUT_TIME=23:59
ATTENDANCE_EXPECTED_CHECKOUT_TIME=17:00

# ============================================
# Report Scheduling
# ============================================
DAILY_REPORT_TIME=22:30
WEEKLY_REPORT_DAY=Sunday
WEEKLY_REPORT_TIME=22:30
DAILY_SUMMARY_TIME=00:00

# ============================================
# Violation Handling
# ============================================
VIOLATION_AUTO_DELETE_MALFORMED=true
VIOLATION_REPEATED_THRESHOLD=3
# Options: escalate_to_manager, log_only, temporary_restriction
VIOLATION_REPEATED_ACTION=escalate_to_manager

# ============================================
# Brand Codes (Comma-separated)
# ============================================
BRAND_CODES=PV,VB,XY,ZZ

# ============================================
# Ticket Format Validation (Regex)
# ============================================
TICKET_FORMAT_REGEX=^[A-Z]{2}-\d{4}-\d+$

# ============================================
# Notification Preferences
# ============================================
NOTIFICATION_SEND_DM=true
NOTIFICATION_SEND_TOPIC_ALERTS=true
NOTIFICATION_INCLUDE_MESSAGE_LINKS=true

# ============================================
# Performance Monitoring
# ============================================
PERFORMANCE_QA_REJECTION_THRESHOLD=0.5
PERFORMANCE_DORMANCY_DAYS=7
PERFORMANCE_LATE_CHECKIN_THRESHOLD=5

# ============================================
# Security
# ============================================
DATABASE_ENCRYPTION_KEY=your-32-character-encryption-key-here
LOG_RETENTION_DAYS=30
AUDIT_TRAIL_RETENTION_DAYS=90

# ============================================
# Feature Flags
# ============================================
FEATURE_AUTO_CHECKOUT=true
FEATURE_AUTO_REMEDIATION=true
FEATURE_PREDICTIVE_ALERTS=true
FEATURE_ANALYTICS_DASHBOARD=true
FEATURE_DAILY_SUMMARY=true
```

### Portability Features

**1. Environment-Based Configuration:**
- All settings in .env file
- No hardcoded values in source code
- Easy to deploy to different environments (dev, staging, production)

**2. Database Abstraction:**
- Switch between SQLite, MongoDB, JSON without code changes
- Migration tools for moving between database types
- Consistent API across all storage backends

**3. Containerization:**
- Docker ensures consistent runtime environment
- No dependency on host system configuration
- Easy to move between servers

**4. Volume Mounts:**
- Data directory mounted as volume
- Logs accessible from host
- Easy backup and restore

**5. Configuration Validation:**
- Startup checks for required environment variables
- Clear error messages for missing/invalid configuration
- Template file with comprehensive documentation

### Monitoring and Maintenance

**Health Checks:**
```python
# Built-in health check endpoint
async def health_check() -> dict:
    return {
        "status": "healthy",
        "database": await check_database_connection(),
        "telegram_api": await check_telegram_api(),
        "scheduler": check_scheduler_status(),
        "uptime": get_uptime()
    }
```

**Logging:**
- Structured JSON logs for easy parsing
- Log rotation with configurable retention
- Separate log files for different components
- Integration with log aggregation tools (ELK, Splunk, CloudWatch)

**Metrics:**
- Message processing rate
- Database query performance
- Notification delivery success rate
- Scheduled job execution time
- Error rates by category

**Alerts:**
- Critical errors sent to Admin Control Panel
- Email/SMS alerts for system failures (optional integration)
- Slack/Discord webhooks for monitoring (optional integration)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

The following properties define the core correctness guarantees of the Telegram Operations Automation System. These properties focus on the pure business logic components that can be tested independently of external services (Telegram API, database I/O). Each property is universally quantified and should hold for all valid inputs.

### Property 1: State Machine Transitions

*For any* task and any valid state transition event (👍 reaction in ASSIGNED state, QA submission in STARTED state, ❤️ reaction in QA_SUBMITTED state, 👎 reaction in QA_SUBMITTED state), the state engine SHALL transition the task to the correct next state according to the state machine definition.

**Validates: Requirements 2.1, 2.2, 2.3, 3.3**

**State Machine Rules:**
- ASSIGNED + 👍 → STARTED
- STARTED + QA_Submission → QA_SUBMITTED
- QA_SUBMITTED + ❤️ → APPROVED
- QA_SUBMITTED + 👎 → REJECTED

### Property 2: Duplicate Task Prevention

*For any* valid TICKET identifier, attempting to create a task with that TICKET when a task with the same TICKET already exists SHALL result in rejection, and the existing task SHALL remain unchanged.

**Validates: Requirements 1.2**

### Property 3: Assignee Extraction

*For any* message text containing one or more @username mentions, the message parser SHALL correctly extract all mentioned usernames, preserving the exact username strings without the @ symbol.

**Validates: Requirements 1.3**

### Property 4: Reaction Idempotence

*For any* task and any reaction type, adding the same reaction multiple times SHALL preserve the timestamp of the first reaction, and subsequent additions of the same reaction type SHALL not modify the task state or transition timestamp.

**Validates: Requirements 2.5**

### Property 5: Reaction Removal Stability

*For any* task with recorded reactions, removing any reaction SHALL not change the task's current state, and all state transitions SHALL remain based solely on reaction additions.

**Validates: Requirements 2.6**

### Property 6: QA Submission Parsing

*For any* message text matching the format [TICKET][BRAND][ASSET] where TICKET, BRAND, and ASSET are non-empty strings, the message parser SHALL extract all three fields correctly, preserving the exact content within each bracket pair.

**Validates: Requirements 3.1**

### Property 7: Latest QA Submission Storage

*For any* TICKET identifier, submitting multiple QA submissions SHALL result in only the most recent submission being stored, with the submission timestamp reflecting the latest submission time.

**Validates: Requirements 3.4**

### Property 8: Format Violation Detection

*For any* message in QA & Review topic that does not match the pattern [TICKET][BRAND][ASSET], the violation detection engine SHALL classify it as a format violation and trigger the configured violation handling action.

**Validates: Requirements 3.6**

### Property 9: Reject Feedback Parsing

*For any* message text matching the format [TICKET][ISSUE_TYPE][PROBLEM][FIX_REQUIRED][ASSIGNEE] where all five fields are non-empty strings, the message parser SHALL extract all five fields correctly, preserving the exact content within each bracket pair.

**Validates: Requirements 4.1**

### Property 10: Rejected Tasks in Reports

*For any* user with one or more tasks in REJECTED state, the daily sync report generated for that user SHALL include all rejected tasks with their associated reject feedback details.

**Validates: Requirements 4.5**

### Property 11: Configuration Parsing Error Reporting

*For any* invalid configuration input (malformed syntax, missing required fields, invalid values), the configuration parser SHALL return a descriptive error message indicating the specific issue and, when applicable, the line number where the error occurred.

**Validates: Requirements 18.2**

### Property 12: Configuration Round-Trip Preservation

*For any* valid Configuration object, the sequence of operations (serialize to text via pretty printer, parse text back to Configuration object) SHALL produce a Configuration object equivalent to the original, preserving all configuration values.

**Validates: Requirements 18.4**

### Testing Implementation Notes

**Property-Based Testing Framework:**
- Use **Hypothesis** (Python property-based testing library)
- Minimum 100 iterations per property test
- Each test tagged with feature name and property number

**Test Tag Format:**
```python
@given(ticket=ticket_strategy(), state=sampled_from(["ASSIGNED", "STARTED", "QA_SUBMITTED"]))
@settings(max_examples=100)
def test_state_machine_transitions(ticket, state):
    """
    Feature: telegram-ops-automation, Property 1: State Machine Transitions
    For any task and any valid state transition event, the state engine SHALL 
    transition the task to the correct next state.
    """
    # Test implementation
```

**Generator Strategies:**
- **Tickets**: Generate valid ticket formats matching TICKET_FORMAT_REGEX
- **Messages**: Generate messages with various bracket patterns and content
- **Usernames**: Generate valid Telegram username strings
- **Reactions**: Sample from valid reaction emoji set
- **Configuration**: Generate valid and invalid configuration structures

**Mocking Strategy:**
- Mock database operations to test pure logic
- Mock Telegram API calls to isolate business logic
- Use in-memory state for fast test execution

**Integration Tests:**
- Separate integration test suite for database operations
- Separate integration test suite for Telegram API interactions
- Use test database (SQLite :memory:) for integration tests

