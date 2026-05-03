# 🚀 Povaly ERP Bot - Telegram Operations Automation System

**Version 1.0.0** | Production Ready | Enterprise-Grade Telegram Automation

A comprehensive enterprise-grade Telegram bot for managing task workflows, QA reviews, attendance tracking, issue management, meeting coordination, and automated reporting with intelligent reaction-based workflows.

## 📋 Table of Contents

- [Overview](#overview)
- [Version 1.0.0 Features](#version-100-features)
- [Core Modules](#core-modules)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Commands](#commands)
- [Topic System](#topic-system)
- [Deployment](#deployment)
- [Database](#database)
- [Security](#security)
- [Support](#support)

---

## 🎯 Overview

Povaly ERP Bot is a production-ready, multi-functional Telegram automation system designed for modern teams to streamline operations through intelligent workflows, automated tracking, and comprehensive reporting.

### What This Bot Does

- **📋 Task Management** - Complete lifecycle from creation to archival with state transitions
- **✅ QA Workflows** - Structured quality assurance with approval/rejection and reversals
- **🐛 Issue Tracking** - Report, claim, resolve issues with priority-based escalation
- **⏰ Attendance System** - Auto check-in, break tracking, leave management with task handover
- **📅 Meeting Coordination** - Schedule meetings, track RSVPs, manage action items
- **🎂 Birthday Celebrations** - Auto wishes, employee info collection, birthday reminders
- **📊 Automated Reporting** - Daily summaries, performance metrics, team analytics
- **🔐 Security & Compliance** - Role-based access, audit trails, violation detection
- **🔄 Smart Reactions** - Emoji-based workflows with reversal support

### Project Status

**Version:** 1.0.0 (Production Ready)  
**Commands:** 89+ commands across all modules  
**Services:** 23+ background services  
**Database Tables:** 23 tables with full relationships  
**Topics:** 12 specialized topics with dedicated guides  
**Reaction System:** Full emoji-based workflow with smart detection  
**Birthday System:** Auto wishes, reminders, and employee info collection

---

## ✨ Version 1.0.0 Features

### 🎯 Task Management System

**Complete Task Lifecycle:**
- ✅ Task creation with auto-generated tickets (POV260501, GSM260502, etc.)
- ✅ Multi-brand support with brand mapper (Povaly, GSMAura, etc.)
- ✅ Multiple assignees per task with workload balancing
- ✅ Task dependencies and blocking relationships
- ✅ Deadline tracking with 24h and 1h reminders
- ✅ Bulk task assignment with smart routing
- ✅ Task state machine with 7 states

**Task States:**
- 🆕 **ASSIGNED** - Task created and assigned
- 🔵 **STARTED** - Work in progress (👍 reaction)
- 🔍 **QA_SUBMITTED** - Submitted for quality review
- ❌ **REJECTED** - QA rejected, needs fixes (👎 reaction)
- ✅ **APPROVED** - QA approved (❤️ reaction)
- 🎉 **COMPLETED** - Assignee confirmed completion (❤️ reaction)
- 📦 **ARCHIVED** - Auto-archived after 24h

**Reaction-Based Workflow:**
- 👍 **Thumbs Up** - Start task (ASSIGNED → STARTED) or mark in progress
- ❤️ **Heart** - QA approval (QA_SUBMITTED → APPROVED) or completion confirmation (APPROVED → COMPLETED)
- 👎 **Thumbs Down** - QA rejection (QA_SUBMITTED → REJECTED)
- 🔥 **Fire** - Mark as urgent/exemption (admin only)

**Flexible Thumbs Up System:**
- ASSIGNED: Start working
- STARTED/QA_SUBMITTED/REJECTED: Use as marker/reminder (no action)
- APPROVED: Not allowed (use ❤️ for completion)
- COMPLETED: Not allowed (already done)

**Smart Features:**
- Auto check-in on first task of the day
- Task archival after 24 hours of completion
- Workload-based assignment
- Expertise-based routing
- Task statistics and analytics

### ✅ QA Review System

**Complete QA Workflow:**
- ✅ QA submission with brand and asset tracking
- ✅ Multiple QA reviewers support
- ✅ Approval/rejection workflow with feedback
- ✅ QA escalation for pending submissions (4 hours)
- ✅ QA reminders for old submissions (2 hours)
- ✅ Reaction-based review process

**QA States:**
- 🟡 **PENDING** - Waiting for reviewer to claim
- 🔵 **IN_REVIEW** - Reviewer is evaluating
- ✅ **APPROVED** - QA passed, task ready for completion
- ❌ **REJECTED** - QA failed, needs fixes

**QA Reactions:**
- 👍 **Claim Review** - Reviewer starts evaluation
- ❤️ **Approve** - QA passed (updates task to APPROVED)
- 👎 **Reject** - QA failed (updates task to REJECTED)

**Reaction Reversal System:**
- Remove 👍: Unclaim review (back to PENDING)
- Remove ❤️: Revert approval (APPROVED → IN_REVIEW)
- Remove 👎: Revert rejection (REJECTED → IN_REVIEW)
- Smart detection: No unclaim if ❤️/👎 added simultaneously

**Auto-Delete DM Notifications:**
- Review started: 60 seconds
- QA approved: 90 seconds
- QA rejected: 90 seconds
- Review unclaimed: 60 seconds
- Approval/rejection reverted: 90 seconds

### 🐛 Issue Management System

**Complete Issue Tracking:**
- ✅ Issue creation linked to tasks
- ✅ Auto-generated issue tickets (POV260501-I1, POV260501-I2)
- ✅ Priority levels (LOW, MEDIUM, HIGH, CRITICAL)
- ✅ Multiple issue handlers (collaboration)
- ✅ Issue claiming and resolution
- ✅ Issue escalation for unclaimed issues (2 hours)
- ✅ Issue reminders for claimed but unresolved (2 hours)

**Issue States:**
- 🔴 **OPEN** - New issue, not claimed
- 🟡 **IN_PROGRESS** - Claimed and being worked on
- ✅ **RESOLVED** - Issue fixed and confirmed
- ❌ **INVALID** - Not a real issue
- 🚨 **ESCALATED** - Overdue, escalated to admins

**Issue Reactions:**
- 👍 **Claim** - Take ownership of issue
- ❤️ **Resolve** - Mark as fixed
- 👎 **Invalid** - Mark as not a real issue

**Reaction Reversal System:**
- Remove 👍: Unclaim issue (back to OPEN)
- Remove ❤️: Unresolve issue (RESOLVED → IN_PROGRESS)
- Remove 👎: Unreject issue (INVALID → IN_PROGRESS)
- Smart detection: No unclaim if ❤️/👎 added simultaneously

**Auto-Delete DM Notifications:**
- Issue claimed: 60 seconds
- Issue resolved: 60 seconds
- Issue rejected: 60 seconds
- Issue unclaimed: 60 seconds
- Resolution/rejection reverted: 60 seconds
- Escalation to admins: 120 seconds

### ⏰ Attendance & Leave System

**Attendance Tracking:**
- ✅ Auto check-in on first task of the day
- ✅ Manual check-in/check-out commands
- ✅ Late check-in detection (after 10:00 AM)
- ✅ Break tracking with start/end times
- ✅ Break limits (max 90 minutes, max 5 breaks)
- ✅ Auto checkout at 23:59
- ✅ Total work hours calculation
- ✅ Monthly attendance reports

**Leave Management:**
- ✅ Leave request submission with date range
- ✅ Replacement user specification
- ✅ Leave approval workflow (❤️ approve, 👎 reject)
- ✅ Automatic task reassignment to replacement
- ✅ Leave status tracking (PENDING, APPROVED, REJECTED)
- ✅ Leave duration validation
- ✅ Overlapping leave detection

**Leave Reactions:**
- ❤️ **Approve** - Approve leave and reassign tasks
- 👎 **Reject** - Reject leave request

**Attendance Commands:**
- `/checkin` - Manual check-in
- `/checkout` - Manual check-out
- `/breakstart` - Start break
- `/breakend` - End break
- `/myattendance` - View your attendance
- `/attendance` - View team attendance (admin)
- `/attendancedetails` - Detailed attendance for specific day

**Leave Commands:**
- `/requestleave` - Request time off
- `/myleave` - View your leave requests
- `/pendingleave` - View pending requests (admin)

### 📅 Meeting System

**Meeting Coordination:**
- ✅ Meeting invitation creation with auto-generated IDs
- ✅ Meeting scheduling with date, time, location
- ✅ Attendee management with special groups (@all, @allactives, @employees)
- ✅ RSVP tracking with reactions
- ✅ Automated reminders (24h, 1h, 15m before meeting)
- ✅ Meeting notes and decisions tracking
- ✅ Action item assignment and tracking
- ✅ Meeting cancellation

**RSVP Reactions:**
- 👍 **I will attend**
- ❤️ **I will attend and I'm prepared**
- 👎 **I cannot attend**
- 🔥 **I have an urgent conflict**

**Action Item Tracking:**
- 👍 **Acknowledged** - I'll do this
- 🔄 **In Progress** - Working on it
- ❤️ **Completed** - Finished
- 👎 **Blocked** - Need help

**Meeting Commands:**
- `/newmeeting` - Create meeting invitation
- `/meetings` - View all meetings
- `/mymeetings` - View meetings you're invited to
- `/meeting` - View meeting details
- `/myactions` - Your action items
- `/actionitems` - All action items (managers)
- `/postmeeting` - Post meeting notes
- `/cancelmeeting` - Cancel a meeting

### 🎂 Birthday & Employee Information System

**Employee Information Collection:**
- ✅ Structured employee info collection via formatted messages
- ✅ First-time user welcome with info request
- ✅ 12 employee fields: NAME, BIRTHDAY, EMAIL, PHONE, DEPARTMENT, POSITION, JOIN_DATE, EMERGENCY_CONTACT, BLOOD_GROUP, ADDRESS, SKILLS, NOTES
- ✅ Validation for email, phone, blood group, date formats
- ✅ Update employee info anytime with `/updateinfo`
- ✅ View employee info with `/myinfo` and `/viewinfo`

**Birthday Celebration System:**
- ✅ Automatic birthday wishes at 9:00 AM daily
- ✅ Birthday wishes sent to user DM + Official Directives topic
- ✅ Custom birthday messages from admins (overrides auto wishes)
- ✅ Birthday reminders 1 day before (6:00 PM)
- ✅ 3-channel reminders: user DM, admin DM, Admin Control Panel
- ✅ Multiple birthdays on same day supported
- ✅ Age display optional (DD-MM-YYYY shows age, DD-MM hides age)
- ✅ Skip birthday celebration with `/skip` command

**Birthday Format:**
- DD-MM-YYYY (e.g., 15-05-1990) - Shows age in wishes
- DD-MM (e.g., 15-05) - Hides age in wishes

**Employee Info Format:**
```
[EMPLOYEE_INFO]
[NAME] John Doe
[BIRTHDAY] 15-05-1990
[EMAIL] john@example.com
[PHONE] +1234567890
[DEPARTMENT] Engineering
[POSITION] Senior Developer
[JOIN_DATE] 01-01-2020
[EMERGENCY_CONTACT] Jane Doe: +0987654321
[BLOOD_GROUP] O+
[ADDRESS] 123 Main St, City
[SKILLS] Python, JavaScript, React
[NOTES] Team lead for backend
```

**Birthday Commands:**
- `/updateinfo` - Update your employee information
- `/myinfo` - View your employee information
- `/mybirthday` - View your birthday info
- `/skip` - Skip your birthday celebration this year
- `/setinfo @user` - Set employee info for user (admin)
- `/viewinfo @user` - View employee info (admin)
- `/birthday @user` - Send custom birthday wish (admin)
- `/birthdays` - View all upcoming birthdays (admin)
- `/birthdaytoday` - View today's birthdays (admin)

**Birthday Features:**
- Auto wishes logged in database (prevents duplicates)
- Reminders logged in database
- Configurable wish and reminder messages
- Enable/disable wishes and reminders via config
- Admin DM recipients configurable
- Birthday wishes use employee's full name (not Telegram username)

### 📊 Automated Reporting

**Daily Reports:**
- ✅ Daily task summary (00:00 GMT+6)
- ✅ Daily sync report (22:30 GMT+6)
- ✅ Task completion statistics
- ✅ Team performance metrics
- ✅ Top performers tracking

**Weekly Reports:**
- ✅ Weekly performance summary (Sunday 22:30 GMT+6)
- ✅ Weekly task statistics
- ✅ Team productivity analysis
- ✅ Trend analysis

**Real-Time Alerts:**
- ✅ Task deadline reminders (24h, 1h before)
- ✅ QA escalation alerts (4 hours pending)
- ✅ Issue escalation alerts (2 hours unclaimed)
- ✅ Meeting reminders (24h, 1h, 15m before)
- ✅ Birthday reminders (1 day before at 6:00 PM)
- ✅ Admin control panel alerts

### 🔐 Security & Access Control

**Role-Based Access Control (5 Roles):**
- 👤 **REGULAR** - Create tasks, submit QA, report issues, check-in/out
- 🎯 **QA_REVIEWER** - Approve/reject QA submissions
- 👔 **MANAGER** - Approve leave, view team workload, escalate issues
- 👑 **ADMIN** - Full system access, manage users, view all data
- 🏆 **OWNER** - System configuration, database management

**Topic-Level Permissions:**
- Restricted topics (admin/manager/owner only):
  - Official Directives
  - Central Archive
  - Daily Sync
  - Admin Control Panel
  - Trash
- Public topics (all users):
  - Task Allocation
  - Core Operations
  - QA & Review
  - Attendance & Leave
  - Boardroom
  - Strategic Lounge

**Security Features:**
- ✅ Granular permissions per topic
- ✅ Format violation detection
- ✅ Comprehensive audit trail
- ✅ Permission violation alerts
- ✅ Encrypted data storage (optional)
- ✅ Message deletion tracking (trash system)

### 🔄 Smart Reaction System

**Intelligent Detection:**
- ✅ Detects reaction changes (👍 → ❤️ = approval, not unclaim)
- ✅ Prevents spam notifications on reaction swaps
- ✅ Supports reaction reversals for all workflows
- ✅ Context-aware reaction handling (Task Allocation vs QA & Review)
- ✅ Auto-delete DM notifications (30-120 seconds based on importance)
- ✅ Plain text DMs to avoid Markdown parsing errors

**Reaction Contexts:**
- Task Allocation topic: Task state transitions
- QA & Review topic: QA approval/rejection
- Core Operations topic: Issue claiming/resolution
- Attendance & Leave topic: Leave approval/rejection
- Boardroom topic: Meeting RSVP and action items
- Admin Control Panel topic: Alert acknowledgment

### 📝 Message Management

**Trash System:**
- ✅ Deleted messages moved to Trash topic (not permanently deleted)
- ✅ Preserves original content, author, timestamp, reason
- ✅ Database sync on task message deletion
- ✅ Prevents accidental data loss
- ✅ Admin audit trail

**Message Editing:**
- ✅ `/edit` command for admins to edit any message
- ✅ Preserves message history
- ✅ Edit confirmation notifications

### 🎨 Brand Management

**Multi-Brand Support:**
- ✅ Brand mapper with configurable brand codes
- ✅ Brand-specific ticket generation
- ✅ Brand-based task routing
- ✅ Brand repository for assets
- ✅ Brand-specific workflows

**Supported Brands:**
- POV (Povaly)
- VRB (VorosaBajar)
- GSM (GSMAura)
- BWN (BWC News)
- BWS (BWC Sportz)
- Custom brands via configuration

---

## 🏗️ Core Modules

### 📦 Module Structure

```
povaly-erp-bot/
├── src/
│   ├── bot/                          # Telegram Bot Layer
│   │   ├── application.py            # Bot application setup
│   │   ├── handlers/                 # Message & command handlers
│   │   │   ├── command_handler.py    # 80+ command handlers
│   │   │   ├── message_handler.py    # Message processing
│   │   │   ├── reaction_handler.py   # Reaction-based workflows
│   │   │   ├── leave_handler.py      # Leave request handling
│   │   │   ├── mytasks_pagination.py # Task list pagination
│   │   │   └── myissues_pagination.py# Issue list pagination
│   │   └── templates/                # Message templates
│   │       └── workflow_templates.py # Workflow message formats
│   │
│   ├── core/                         # Business Logic Layer
│   │   ├── brand_mapper.py           # Brand code mapping
│   │   ├── ticket_generator.py       # Ticket ID generation
│   │   ├── violation_detector.py     # Format violation detection
│   │   ├── parser/                   # Message parsers
│   │   │   ├── message_parser.py     # Task message parsing
│   │   │   ├── issue_parser.py       # Issue message parsing
│   │   │   └── meeting_parser.py     # Meeting message parsing
│   │   └── state/                    # State management
│   │       └── state_engine.py       # Task state machine
│   │
│   ├── services/                     # Service Layer (23+ services)
│   │   ├── task_service.py           # Task management
│   │   ├── qa_service.py             # QA workflow
│   │   ├── issue_service.py          # Issue tracking
│   │   ├── attendance_service.py     # Attendance tracking
│   │   ├── leave_request_service.py  # Leave management
│   │   ├── meeting_service.py        # Meeting coordination
│   │   ├── employee_info_service.py  # Employee info collection
│   │   ├── birthday_service.py       # Birthday wishes and reminders
│   │   ├── birthday_scheduler.py     # Birthday automation
│   │   ├── archive_service.py        # Task archival
│   │   ├── escalation_service.py     # Task escalation
│   │   ├── qa_escalation_service.py  # QA escalation
│   │   ├── deadline_reminder_service.py # Deadline reminders
│   │   ├── meeting_reminder_service.py  # Meeting reminders
│   │   ├── daily_summary_service.py  # Daily reports
│   │   ├── database_sync_service.py  # Database synchronization
│   │   ├── reaction_sync_service.py  # Reaction tracking
│   │   ├── report_service.py         # Report generation
│   │   ├── topic_scanner_service.py  # Topic scanning
│   │   ├── violation_tracking_service.py # Violation tracking
│   │   └── security_alert_service.py # Security alerts
│   │
│   ├── data/                         # Data Access Layer
│   │   ├── adapters/                 # Database adapters
│   │   │   ├── sqlite_adapter.py     # SQLite implementation
│   │   │   └── factory.py            # Adapter factory
│   │   ├── models/                   # Data models (21 tables)
│   │   │   ├── task.py               # Task model
│   │   │   ├── user.py               # User model
│   │   │   ├── issue.py              # Issue model
│   │   │   ├── qa_submission.py      # QA submission model
│   │   │   ├── attendance.py         # Attendance model
│   │   │   ├── leave_request.py      # Leave request model
│   │   │   ├── meeting.py            # Meeting model
│   │   │   ├── break_record.py       # Break record model
│   │   │   ├── admin_alert.py        # Admin alert model
│   │   │   ├── audit_trail.py        # Audit trail model
│   │   │   ├── violation.py          # Violation model
│   │   │   └── report.py             # Report model
│   │   ├── repositories/             # Data repositories (14 repos)
│   │   │   ├── task_repository.py
│   │   │   ├── user_repository.py    # Includes employee info methods
│   │   │   ├── issue_repository.py
│   │   │   ├── qa_repository.py
│   │   │   ├── attendance_repository.py
│   │   │   ├── meeting_repository.py
│   │   │   ├── admin_alert_repository.py
│   │   │   ├── audit_trail_repository.py
│   │   │   ├── reaction_repository.py
│   │   │   ├── task_assignee_repository.py
│   │   │   └── base_repository.py
│   │   └── migrations/               # Database migrations (11 migrations)
│   │       ├── migration_001_comprehensive_redesign.py
│   │       ├── migration_002_add_timestamp_to_reactions.py
│   │       ├── migration_003_fix_task_reactions.py
│   │       ├── migration_004_add_issue_ticket.py
│   │       ├── migration_005_fix_issue_constraints.py
│   │       ├── migration_006_add_break_records.py
│   │       ├── migration_007_add_admin_alerts.py
│   │       ├── migration_008_add_task_dependencies.py
│   │       ├── migration_009_add_meetings.py
│   │       ├── migration_010_add_task_deadline.py
│   │       └── migration_011_add_employee_info.py
│   │
│   ├── security/                     # Security Layer
│   │   └── access_control.py         # Role-based access control
│   │
│   ├── utils/                        # Utility Layer
│   │   ├── message_utils.py          # Message utilities
│   │   ├── link_builder.py           # Message link builder
│   │   ├── format_utils.py           # Format utilities
│   │   ├── time_utils.py             # Time utilities
│   │   ├── validators.py             # Input validators
│   │   ├── logger.py                 # Logging utilities
│   │   └── admin_alert_helper.py     # Admin alert helpers
│   │
│   ├── config.py                     # Configuration management
│   └── main.py                       # Application entry point
│
├── data/                             # Data directory
│   ├── povaly_erp_bot.db            # SQLite database
│   ├── backups/                      # Database backups
│   └── logs/                         # Application logs
│       ├── telegram_bot.log          # Bot logs
│       └── errors.log                # Error logs
│
├── docs/                             # Documentation (15 guides)
│   ├── GUIDE_TASK_ALLOCATION.txt     # Task management guide
│   ├── GUIDE_QA_REVIEW.txt           # QA workflow guide
│   ├── GUIDE_CORE_OPERATIONS.txt     # Issue tracking guide
│   ├── GUIDE_ATTENDANCE_LEAVE.txt    # Attendance guide
│   ├── GUIDE_BOARDROOM.txt           # Meeting guide
│   ├── GUIDE_BIRTHDAY_SYSTEM.md      # Birthday system user guide
│   ├── GUIDE_BIRTHDAY_ADMIN.md       # Birthday admin guide
│   ├── BIRTHDAY_QUICK_REFERENCE.md   # Birthday quick reference
│   ├── GUIDE_ADMIN_CONTROL_PANEL.txt # Admin guide
│   ├── GUIDE_BRAND_REPOSITORY.txt    # Brand assets guide
│   ├── GUIDE_CENTRAL_ARCHIVE.txt     # Archive guide
│   ├── GUIDE_DAILY_SYNC.txt          # Daily sync guide
│   ├── GUIDE_OFFICIAL_DIRECTIVES.txt # Directives guide
│   ├── GUIDE_STRATEGIC_LOUNGE.txt    # Strategy guide
│   └── PINNING_INSTRUCTIONS.txt      # Pinning guide
│
├── scripts/                          # Utility scripts
│   └── generate_project_structure.py # Project structure generator
│
├── .env                              # Environment variables
├── .env.template                     # Environment template
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Docker configuration
├── docker-compose.yml                # Docker Compose configuration
├── Makefile                          # Build automation
├── pytest.ini                        # Test configuration
├── setup.py                          # Package setup
├── install.sh                        # Installation script
├── run.sh                            # Run script
├── check_bot.sh                      # Bot status check
├── BOT_MANAGEMENT.md                 # Bot management guide
└── README.md                         # This file
```

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Telegram Bot API                             │
│                    (python-telegram-bot v20+)                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      Telegram Bot Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Command    │  │   Message    │  │      Reaction            │  │
│  │   Handler    │  │   Handler    │  │      Handler             │  │
│  │  (80+ cmds)  │  │  (Parsing)   │  │  (Emoji Workflows)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                     Business Logic Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │   Task   │  │    QA    │  │  Issue   │  │    Attendance    │   │
│  │  Service │  │ Service  │  │ Service  │  │     Service      │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Meeting  │  │  Leave   │  │  Brand   │  │     Security     │   │
│  │ Service  │  │ Service  │  │  Mapper  │  │  Access Control  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    Background Services Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Archive    │  │  Escalation  │  │    QA Escalation         │  │
│  │   Service    │  │   Service    │  │      Service             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Deadline   │  │   Meeting    │  │   Daily Summary          │  │
│  │   Reminder   │  │   Reminder   │  │     Service              │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Database   │  │   Reaction   │  │      Report              │  │
│  │     Sync     │  │     Sync     │  │      Service             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      Data Access Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │     Task     │  │     User     │  │       Issue              │  │
│  │  Repository  │  │  Repository  │  │     Repository           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │      QA      │  │  Attendance  │  │      Meeting             │  │
│  │  Repository  │  │  Repository  │  │     Repository           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Admin Alert  │  │ Audit Trail  │  │     Reaction             │  │
│  │  Repository  │  │  Repository  │  │     Repository           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       Database Adapter Layer                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              SQLite Adapter (Default)                        │   │
│  │  - File-based storage                                        │   │
│  │  - No external dependencies                                  │   │
│  │  - Automatic migrations                                      │   │
│  │  - Backup support                                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                         Database Layer                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    SQLite Database                           │   │
│  │  - 21 tables with full relationships                         │   │
│  │  - Foreign key constraints                                   │   │
│  │  - Indexes for performance                                   │   │
│  │  - Transaction support                                       │   │
│  │  - Automatic backups                                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Message → Telegram API → Bot Handler → Parser → Service → Repository → Database
                                    ↓
                              Reaction Handler → State Engine → Service → Repository
                                    ↓
                              Background Services (Schedulers, Escalation, Reminders)
                                    ↓
                              Notification → Telegram API → User DM/Group Message
```

---

## 📦 Installation

### Prerequisites

- **Python 3.9+** (Tested on 3.9, 3.10, 3.11)
- **Telegram Bot Token** (from @BotFather)
- **Telegram Group** with Topics enabled
- **Git** for version control
- **pip** for package management

### Quick Start (5 Minutes)

1. **Clone Repository**
```bash
git clone https://github.com/povalygroup/povaly-erp-bot.git
cd povaly-erp-bot
```

2. **Install Dependencies**
```bash
# Linux/Mac
./install.sh

# Windows
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
# Copy template
cp .env.template .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

4. **Start Bot**
```bash
# Linux/Mac
./run.sh

# Windows
python src/main.py

# Background (Linux/Mac)
nohup python src/main.py > bot.log 2>&1 &
```

5. **Verify Bot is Running**
```bash
# Check bot status
./check_bot.sh

# View logs
tail -f data/logs/telegram_bot.log
```

### Docker Deployment

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Development Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python src/main.py
```

---

## ⚙️ Configuration

### Required Environment Variables

```env
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_GROUP_ID=your_group_id_here

# Database
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/povaly_erp_bot.db
DATABASE_ENCRYPTION_KEY=your_32_char_encryption_key_here

# User Roles (comma-separated Telegram user IDs)
ADMINISTRATORS=123456789,987654321
MANAGERS=111111111,222222222
QA_REVIEWERS=333333333,444444444
OWNERS=555555555

# Topic IDs (comma-separated)
TOPIC_OFFICIAL_DIRECTIVES=1
TOPIC_BRAND_REPOSITORY=2
TOPIC_TASK_ALLOCATION=3
TOPIC_CORE_OPERATIONS=4
TOPIC_QA_REVIEW=5
TOPIC_CENTRAL_ARCHIVE=6
TOPIC_DAILY_SYNC=7
TOPIC_ATTENDANCE_LEAVE=8
TOPIC_ADMIN_CONTROL_PANEL=9
TOPIC_BOARDROOM=10
TOPIC_STRATEGIC_LOUNGE=11
TOPIC_TRASH=12

# Brand Codes
BRAND_CODES=POV,VRB,GSM,BWN,BWS

# Timezone
TIMEZONE=GMT+6

# Feature Flags
ENABLE_AUTO_ASSIGN=false
PREFER_EXPERTISE=true
FEATURE_AUTO_CHECKOUT=true
FEATURE_DAILY_SUMMARY=true
```

### Optional Configuration

```env
# Inactivity Thresholds (hours)
INACTIVITY_WARNING_HOURS=18
INACTIVITY_MARK_HOURS=24
INACTIVITY_ESCALATE_HOURS=48
INACTIVITY_CRITICAL_HOURS=72

# Attendance
ATTENDANCE_LATE_CHECKIN_TIME=11:00
ATTENDANCE_AUTO_CHECKOUT_TIME=23:59
ATTENDANCE_MAX_BREAK_TIME_MINUTES=90
ATTENDANCE_MAX_BREAK_COUNT=5

# QA
QA_ESCALATION_HOURS=24
QA_REMINDER_HOURS=12

# Leave Requests
LEAVE_REQUEST_MIN_NOTICE_DAYS=0
LEAVE_REQUEST_MAX_DURATION_DAYS=30
LEAVE_REQUEST_AUTO_REASSIGN_TASKS=true

# Reports
DAILY_REPORT_TIME=22:30
WEEKLY_REPORT_DAY=Sunday
WEEKLY_REPORT_TIME=22:30
DAILY_SUMMARY_TIME=00:00

# Birthday System
BIRTHDAY_WISHES_ENABLED=true
BIRTHDAY_REMINDERS_ENABLED=true
BIRTHDAY_WISH_TIME=09:00
BIRTHDAY_REMINDER_TIME=18:00
BIRTHDAY_WISH_MESSAGE=🎉 Happy Birthday {name}! 🎂\n\nWishing you a wonderful day filled with joy and happiness! 🎈
BIRTHDAY_REMINDER_MESSAGE=📅 Reminder: Tomorrow is {name}'s birthday! 🎂
ADMIN_DM_RECIPIENTS=123456789,987654321
EMPLOYEE_INFO_WELCOME_MESSAGE=Welcome! Please share your employee information using the format shown in the guide.
```

---

## 🎮 Usage

### Basic Workflow Example

**1. Create a Task**
```
/newtask
→ Bot shows brand selection buttons
→ Select brand (e.g., Povaly)
→ Enter task details in format:
   [TASK] Task description
   [ASSIGNEE] @username
   [DEADLINE] 2026-05-10
→ Task created with ticket #POV260501
```

**2. Start Working**
```
→ React with 👍 on task message
→ Status changes: ASSIGNED → STARTED
→ Auto check-in recorded (if first task of day)
→ DM confirmation sent
```

**3. Submit for QA**
```
/newqa
→ Select task from list
→ Enter QA submission:
   [TICKET] POV260501
   [BRAND] #Povaly
   [ASSET] https://link-to-deliverable
→ QA submission created
→ Waiting for reviewer
```

**4. QA Review**
```
→ Reviewer reacts with 👍 to claim
→ Submitter gets DM: "Review started"
→ Reviewer evaluates work
→ Reviewer reacts with ❤️ to approve
→ Task status: QA_SUBMITTED → APPROVED
→ Submitter gets DM: "QA approved"
```

**5. Confirm Completion**
```
→ Assignee reacts with ❤️ on task message
→ Task status: APPROVED → COMPLETED
→ DM confirmation sent
→ Task will auto-archive in 24 hours
```

### Common Workflows

**Report an Issue:**
```
/newissue
→ Enter issue details:
   [TICKET] POV260501
   [ISSUE] Bug description
   [DETAILS] Detailed explanation
   [PRIORITY] HIGH
→ Issue created with ticket #POV260501-I1
→ Team can claim with 👍 reaction
```

**Request Leave:**
```
/requestleave 2026-05-15 2026-05-20 Vacation @replacement_user
→ Leave request created
→ Manager reviews and reacts ❤️ to approve
→ Tasks automatically reassigned to replacement
→ Approval DM sent
```

**Schedule Meeting:**
```
/newmeeting
→ Enter meeting details:
   [MEETING_INVITE] Q2 Planning
   [DATE] 2026-05-15
   [TIME] 10:00 - 11:30 GMT+6
   [ATTENDEES] @user1, @user2, @all
   [AGENDA] Q2 goals, resources, timeline
→ Meeting created with auto-generated ID
→ Reminders sent at 24h, 1h, 15m before
```

### Quick Commands Reference

```bash
# Task Management
/newtask              # Create new task
/mytasks              # View your tasks
/tasksbystate         # View tasks by state
/overduetasks         # View overdue tasks
/taskstats            # View task statistics

# QA Workflow
/newqa                # Submit for QA
/myqa                 # View your QA submissions
/pendingqa            # View pending QA (reviewers)
/reviewingqa          # View QAs you're reviewing
/unreviewedqa         # View unreviewed QAs

# Issue Tracking
/newissue             # Create new issue
/myissues             # View issues you created
/myclaimedissues      # View issues you're handling
/openissues           # View all open issues

# Attendance
/checkin              # Manual check-in
/checkout             # Manual check-out
/breakstart           # Start break
/breakend             # End break
/myattendance         # View your attendance

# Leave Management
/requestleave         # Request time off
/myleave              # View your leave requests
/pendingleave         # View pending requests (admin)

# Meetings
/newmeeting           # Create meeting
/meetings             # View all meetings
/mymeetings           # View your meetings
/myactions            # View your action items

# Birthday & Employee Info
/updateinfo           # Update your employee info
/myinfo               # View your employee info
/mybirthday           # View your birthday info
/birthdays            # View upcoming birthdays (admin)
/birthdaytoday        # View today's birthdays (admin)

# General
/help                 # Show help
/commands             # Show all commands
/guide                # Show topic guides
```

---

## 📚 Commands

### Complete Command List (80+ Commands)

#### Task Management Commands (20+)
- `/newtask` - Create new task with template
- `/mytasks` - View your assigned tasks with pagination
- `/tasksbystate [STATE]` - View tasks filtered by state
- `/overduetasks` - View overdue tasks
- `/taskstats` - View task statistics
- `/task #TICKET` - View specific task details
- `/assignto @user #TICKET` - Assign task to user
- `/bulkassign @user #TICKET1 #TICKET2` - Bulk assign tasks
- `/reassign #TICKET @newuser` - Reassign task
- `/block #TICKET1 #TICKET2` - Create task dependency
- `/unblock #TICKET1 #TICKET2` - Remove task dependency
- `/setdeadline #TICKET YYYY-MM-DD` - Set task deadline
- `/removedeadline #TICKET` - Remove task deadline
- `/workload [@user]` - View workload statistics
- `/scantopic` - Scan topic for tasks and sync database
- `/syncdb` - Sync database with Telegram messages
- `/taskhelp` - Task management quick reference

#### QA Review Commands (10+)
- `/newqa` - Submit work for QA review
- `/submitqa` - Submit work for QA (alias)
- `/myqa` - View your QA submissions
- `/pendingqa` - View pending QA submissions (reviewers)
- `/reviewingqa` - View QAs you're currently reviewing
- `/unreviewedqa` - View unreviewed QA submissions
- `/qa #TICKET` - View QA submission details
- `/approve #TICKET` - Approve QA submission
- `/reject #TICKET REASON` - Reject QA with reason
- `/reopenqa #TICKET` - Reopen rejected QA
- `/qahelp` - QA workflow quick reference

#### Issue Management Commands (10+)
- `/newissue` - Create new issue with template
- `/myissues` - View issues you created
- `/myclaimedissues` - View issues you're handling
- `/openissues` - View all unresolved issues
- `/issue #TICKET` - View issue details
- `/close #TICKET` - Mark issue as resolved
- `/reopen #TICKET` - Reopen closed issue
- `/unresolved` - View claimed but unresolved issues
- `/inactive` - View unclaimed issues
- `/issuehelp` - Issue tracking quick reference

#### Attendance Commands (10+)
- `/checkin` - Manual check-in
- `/checkout` - Manual check-out
- `/breakstart` - Start break
- `/breakend` - End break
- `/mybreaks` - View today's breaks
- `/myattendance [YYYY-MM]` - View your attendance
- `/attendance @user [YYYY-MM]` - View user attendance (admin)
- `/attendancedetails YYYY-MM-DD` - Detailed attendance for specific day
- `/teamattendance` - View team attendance summary (admin)
- `/attendancehelp` - Attendance quick reference

#### Leave Management Commands (5+)
- `/requestleave START END REASON [@replacement]` - Request time off
- `/myleave` - View your leave requests
- `/pendingleave` - View pending leave requests (admin)
- `/approveleave #ID` - Approve leave request (admin)
- `/rejectleave #ID REASON` - Reject leave request (admin)

#### Meeting Commands (10+)
- `/newmeeting` - Create meeting invitation
- `/meetings` - View all upcoming meetings
- `/mymeetings` - View meetings you're invited to
- `/meeting <ID or title>` - View meeting details
- `/myactions` - View your action items from meetings
- `/actionitems` - View all action items (managers)
- `/actionstatus` - View action item status
- `/postmeeting` - Post meeting notes template
- `/cancelmeeting MTG-ID` - Cancel a meeting
- `/meetinghelp` - Meeting coordination quick reference

#### Birthday & Employee Info Commands (9)
- `/updateinfo` - Update your employee information
- `/myinfo` - View your employee information
- `/mybirthday` - View your birthday information
- `/skip` - Skip your birthday celebration this year
- `/setinfo @user` - Set employee info for user (admin)
- `/viewinfo @user` - View employee info for user (admin)
- `/birthday @user [message]` - Send custom birthday wish (admin)
- `/birthdays` - View all upcoming birthdays (admin)
- `/birthdaytoday` - View today's birthdays (admin)

#### Admin Commands (15+)
- `/workload [@user]` - View workload statistics
- `/assignto @user #TICKET` - Assign task to user
- `/bulkassign @user #TICKET1 #TICKET2` - Bulk assign multiple tasks
- `/pendingleave` - View pending leave requests
- `/attendance @user [YYYY-MM]` - View user attendance
- `/teamattendance` - View team attendance summary
- `/scantopic` - Scan topic and sync database
- `/syncdb` - Force database synchronization
- `/edit` - Edit any message (reply to message with /edit new content)
- `/resetdb` - Reset database (dangerous!)
- `/backup` - Create database backup
- `/restore BACKUP_FILE` - Restore from backup
- `/stats` - View system statistics
- `/alerts` - View admin alerts
- `/adminhelp` - Admin commands quick reference

#### General Commands (11+)
- `/start` - Start bot and show welcome message
- `/help` - Show help information
- `/commands` - Show all available commands (role-filtered)
- `/guide` - Show topic guides
- `/taskhelp` - Task management guide
- `/qahelp` - QA workflow guide
- `/issuehelp` - Issue tracking guide
- `/attendancehelp` - Attendance guide
- `/meetinghelp` - Meeting guide
- `/birthdayhelp` - Birthday system guide
- `/adminhelp` - Admin commands guide

---

## 🏢 Topic System

### 12 Specialized Topics

The bot operates across 12 specialized Telegram topics, each with dedicated functionality and guides:

#### 1. 📢 Official Directives
**Purpose:** Company announcements, policies, and official communications  
**Access:** Admin/Manager/Owner only (posting)  
**Features:**
- Company-wide announcements
- Policy updates
- Official decisions
- Compliance notices

#### 2. 🎨 Brand Repository
**Purpose:** Brand assets, guidelines, and resources  
**Access:** All users (read), Admin/Manager (post)  
**Features:**
- Brand guidelines storage
- Asset library
- Logo and design resources
- Brand-specific documentation

#### 3. 📋 Task Allocation
**Purpose:** Task creation, assignment, and tracking  
**Access:** All users  
**Features:**
- Task creation with `/newtask`
- Reaction-based state transitions (👍 start, ❤️ complete)
- Multiple assignees support
- Task dependencies and blocking
- Deadline tracking
- Bulk assignment
- Task statistics

**Reactions:**
- 👍 Start task (ASSIGNED → STARTED)
- ❤️ Confirm completion (APPROVED → COMPLETED)
- 🔥 Mark as urgent (admin only)

#### 4. 🐛 Core Operations
**Purpose:** Issue reporting and resolution  
**Access:** All users  
**Features:**
- Issue creation with `/newissue`
- Priority levels (LOW, MEDIUM, HIGH, CRITICAL)
- Issue claiming with 👍 reaction
- Issue resolution with ❤️ reaction
- Issue escalation (2 hours)
- Multiple handlers support

**Reactions:**
- 👍 Claim issue
- ❤️ Resolve issue
- 👎 Mark as invalid

#### 5. ✅ QA & Review
**Purpose:** Quality assurance submissions and reviews  
**Access:** All users (submit), QA Reviewers (review)  
**Features:**
- QA submission with `/newqa`
- Reviewer claiming with 👍 reaction
- Approval/rejection workflow
- QA escalation (4 hours)
- Reaction reversal support

**Reactions:**
- 👍 Claim for review
- ❤️ Approve QA
- 👎 Reject QA

#### 6. 📦 Central Archive
**Purpose:** Completed tasks archive  
**Access:** Admin/Manager/Owner only (posting)  
**Features:**
- Auto-archival of completed tasks (24h after completion)
- Task completion history
- Performance tracking
- Searchable archive

#### 7. 📊 Daily Sync
**Purpose:** Daily reports and summaries  
**Access:** Admin/Manager/Owner only (posting)  
**Features:**
- Daily task summary (00:00 GMT+6)
- Daily sync report (22:30 GMT+6)
- Weekly performance report (Sunday 22:30)
- Team statistics
- Top performers

#### 8. ⏰ Attendance & Leave
**Purpose:** Attendance tracking and leave management  
**Access:** All users  
**Features:**
- Auto check-in on first task
- Manual check-in/checkout
- Break tracking
- Leave requests with `/requestleave`
- Leave approval workflow (❤️ approve, 👎 reject)
- Task reassignment during leave

**Reactions:**
- ❤️ Approve leave request (admin)
- 👎 Reject leave request (admin)

#### 9. 👑 Admin Control Panel
**Purpose:** Admin alerts and system notifications  
**Access:** Admin/Manager/Owner only  
**Features:**
- Task escalation alerts
- QA escalation alerts
- Issue escalation alerts
- System notifications
- Security alerts
- Violation reports

**Reactions:**
- 👍 Acknowledge alert
- ❤️ Mark as resolved

#### 10. 📅 Boardroom
**Purpose:** Meeting coordination and notes  
**Access:** All users  
**Features:**
- Meeting invitations with `/newmeeting`
- RSVP tracking (👍 attend, ❤️ prepared, 👎 cannot attend)
- Automated reminders (24h, 1h, 15m)
- Meeting notes
- Action item tracking
- Decision tracking

**Reactions:**
- 👍 I will attend
- ❤️ I will attend and I'm prepared
- 👎 I cannot attend
- 🔥 I have an urgent conflict

#### 11. 💡 Strategic Lounge
**Purpose:** Strategy discussions and planning  
**Access:** All users  
**Features:**
- Open discussions
- Strategy planning
- Brainstorming
- Team collaboration

#### 12. 🗑️ Trash
**Purpose:** Deleted messages archive  
**Access:** Admin/Manager/Owner only  
**Features:**
- Preserves deleted messages
- Tracks deletion reason
- Maintains audit trail
- Prevents accidental data loss

### Topic Guides

Each topic has a comprehensive guide document in the `docs/` folder:
- `GUIDE_TASK_ALLOCATION.txt` - Complete task management guide
- `GUIDE_QA_REVIEW.txt` - QA workflow and reactions guide
- `GUIDE_CORE_OPERATIONS.txt` - Issue tracking guide
- `GUIDE_ATTENDANCE_LEAVE.txt` - Attendance and leave guide
- `GUIDE_BOARDROOM.txt` - Meeting coordination guide
- `GUIDE_BIRTHDAY_SYSTEM.md` - Birthday system user guide
- `GUIDE_BIRTHDAY_ADMIN.md` - Birthday admin guide with troubleshooting
- `BIRTHDAY_QUICK_REFERENCE.md` - Birthday quick reference card
- `GUIDE_ADMIN_CONTROL_PANEL.txt` - Admin features guide
- `GUIDE_BRAND_REPOSITORY.txt` - Brand assets guide
- `GUIDE_CENTRAL_ARCHIVE.txt` - Archive guide
- `GUIDE_DAILY_SYNC.txt` - Reports guide
- `GUIDE_OFFICIAL_DIRECTIVES.txt` - Directives guide
- `GUIDE_STRATEGIC_LOUNGE.txt` - Strategy guide
- `PINNING_INSTRUCTIONS.txt` - How to pin guides

Access guides in bot with `/guide` command or view them in the `docs/` folder.

---

## 🚀 Deployment

### Production Deployment (Hostinger VPS)

**Server Details:**
- Host: `145.79.25.42`
- Port: `65002`
- Path: `/home/u531179370/povaly-bot/povaly-erp-bot/`

**Deployment Steps:**

1. **SSH into Server**
```bash
ssh user@145.79.25.42 -p 65002
cd /home/u531179370/povaly-bot/povaly-erp-bot/
```

2. **Pull Latest Changes**
```bash
git pull origin main
```

3. **Restart Bot**
```bash
# Stop bot
./stop_bot.sh

# Start bot in background
./start_bot_forever.sh

# Or use nohup
nohup python src/main.py > bot.log 2>&1 &
```

4. **Verify Bot Status**
```bash
# Check if bot is running
./check_bot.sh

# View logs
tail -f data/logs/telegram_bot.log

# View errors
tail -f data/logs/errors.log
```

5. **Monitor Bot**
```bash
# View real-time logs
tail -f data/logs/telegram_bot.log

# Check process
ps aux | grep python

# Check bot status in Telegram
# Send /help to bot
```

### Docker Deployment

**Using Docker Compose:**

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# View specific service logs
docker-compose logs -f bot

# Execute commands in container
docker-compose exec bot python src/main.py
```

**Using Docker:**

```bash
# Build image
docker build -t povaly-erp-bot .

# Run container
docker run -d \
  --name povaly-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  povaly-erp-bot

# View logs
docker logs -f povaly-bot

# Stop container
docker stop povaly-bot

# Remove container
docker rm povaly-bot
```

### Local Development

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run bot
python src/main.py

# Run with auto-reload (development)
# Install watchdog: pip install watchdog
watchmedo auto-restart --patterns="*.py" --recursive python src/main.py
```

### Systemd Service (Linux)

Create `/etc/systemd/system/povaly-bot.service`:

```ini
[Unit]
Description=Povaly ERP Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/povaly-erp-bot
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable povaly-bot
sudo systemctl start povaly-bot

# View status
sudo systemctl status povaly-bot

# View logs
sudo journalctl -u povaly-bot -f

# Restart service
sudo systemctl restart povaly-bot
```

---

## 💾 Database

### Database Schema (23 Tables)

**Core Tables:**
1. **users** - User profiles, roles, and employee information (27 new fields)
2. **tasks** - Task records with state tracking
3. **task_assignees** - Multiple assignees per task
4. **task_dependencies** - Task blocking relationships
5. **task_reactions** - Reaction tracking for tasks
6. **issues** - Issue records with priority
7. **qa_submissions** - QA submission records
8. **attendance** - Daily attendance records
9. **break_records** - Break tracking
10. **leave_requests** - Leave request records
11. **meetings** - Meeting records
12. **meeting_attendees** - Meeting attendance tracking
13. **action_items** - Meeting action items
14. **birthday_wishes** - Birthday wish log (prevents duplicates)
15. **birthday_reminders** - Birthday reminder log
16. **admin_alerts** - Admin notification records
17. **audit_trail** - Comprehensive audit log
18. **violations** - Format violation records
19. **reports** - Generated report records
20. **reactions** - Global reaction tracking
21. **user_expertise** - User skill tracking
22. **brand_mapping** - Brand code mapping
23. **system_config** - System configuration

### Database Operations

**Backup Database:**
```bash
# Automatic backup (runs daily at 23:00 GMT+6)
# Backups stored in data/backups/

# Manual backup
cp data/povaly_erp_bot.db data/backups/povaly_erp_bot_backup_$(date +%Y%m%d_%H%M%S).db

# Windows PowerShell
cp data/povaly_erp_bot.db data/backups/povaly_erp_bot_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db
```

**Restore Database:**
```bash
# Stop bot first
./stop_bot.sh

# Restore from backup
cp data/backups/povaly_erp_bot_backup_20260503_135337.db data/povaly_erp_bot.db

# Start bot
./start_bot_forever.sh
```

**Clear Database (Development Only):**
```bash
# WARNING: This will delete all data!

# Stop bot
./stop_bot.sh

# Remove database
rm data/povaly_erp_bot.db

# Start bot (will create fresh database)
python src/main.py
```

**Inspect Database:**
```bash
# Using sqlite3
sqlite3 data/povaly_erp_bot.db

# View tables
.tables

# View schema
.schema tasks

# Query data
SELECT * FROM tasks LIMIT 10;

# Exit
.quit
```

**Export/Import Data:**
```bash
# Export to SQL
sqlite3 data/povaly_erp_bot.db .dump > backup.sql

# Import from SQL
sqlite3 data/povaly_erp_bot.db < backup.sql

# Export to CSV
sqlite3 -header -csv data/povaly_erp_bot.db "SELECT * FROM tasks;" > tasks.csv
```

### Database Migrations

The bot automatically runs migrations on startup. Migrations are located in `src/data/migrations/`:

1. `migration_001_comprehensive_redesign.py` - Initial schema
2. `migration_002_add_timestamp_to_reactions.py` - Reaction timestamps
3. `migration_003_fix_task_reactions.py` - Task reaction fixes
4. `migration_004_add_issue_ticket.py` - Issue ticket support
5. `migration_005_fix_issue_constraints.py` - Issue constraint fixes
6. `migration_006_add_break_records.py` - Break tracking
7. `migration_007_add_admin_alerts.py` - Admin alerts
8. `migration_008_add_task_dependencies.py` - Task dependencies
9. `migration_009_add_meetings.py` - Meeting system
10. `migration_010_add_task_deadline.py` - Task deadlines
11. `migration_011_add_employee_info.py` - Employee info and birthday system

**Migration Status:**
- Migrations run automatically on bot startup
- Migration history tracked in `migrations` table
- Failed migrations logged to `data/logs/errors.log`

### Supported Databases

**SQLite (Default):**
- File-based storage
- No external dependencies
- Automatic migrations
- Backup support
- Perfect for small to medium teams (up to 100 users)

**MongoDB (Optional):**
- Document-based storage
- Scalable for large teams
- Requires MongoDB server
- Configure in `.env`: `DATABASE_TYPE=mongodb`

**JSON (Optional):**
- Simple file-based storage
- Good for testing
- Not recommended for production
- Configure in `.env`: `DATABASE_TYPE=json`

---

## 🔐 Security

### Role-Based Access Control (RBAC)

**5 User Roles:**

| Role | Level | Permissions |
|------|-------|-------------|
| **👤 REGULAR** | 1 | Create tasks, submit QA, report issues, check-in/out, view own data |
| **🎯 QA_REVIEWER** | 2 | All REGULAR + Approve/reject QA submissions, view QA statistics |
| **👔 MANAGER** | 3 | All QA_REVIEWER + Approve leave, view team workload, bulk assign, escalate issues |
| **👑 ADMIN** | 4 | All MANAGER + Full system access, manage users, view all data, edit messages, system configuration |
| **🏆 OWNER** | 5 | All ADMIN + Database management, system reset, backup/restore, critical operations |

**Permission Matrix:**

| Action | Regular | QA Reviewer | Manager | Admin | Owner |
|--------|---------|-------------|---------|-------|-------|
| Create Task | ✅ | ✅ | ✅ | ✅ | ✅ |
| Start Task | ✅ | ✅ | ✅ | ✅ | ✅ |
| Submit QA | ✅ | ✅ | ✅ | ✅ | ✅ |
| Approve QA | ❌ | ✅ | ✅ | ✅ | ✅ |
| Report Issue | ✅ | ✅ | ✅ | ✅ | ✅ |
| Claim Issue | ✅ | ✅ | ✅ | ✅ | ✅ |
| Check-in/out | ✅ | ✅ | ✅ | ✅ | ✅ |
| Request Leave | ✅ | ✅ | ✅ | ✅ | ✅ |
| Approve Leave | ❌ | ❌ | ✅ | ✅ | ✅ |
| View Team Workload | ❌ | ❌ | ✅ | ✅ | ✅ |
| Bulk Assign | ❌ | ❌ | ✅ | ✅ | ✅ |
| Edit Messages | ❌ | ❌ | ❌ | ✅ | ✅ |
| System Config | ❌ | ❌ | ❌ | ✅ | ✅ |
| Database Management | ❌ | ❌ | ❌ | ❌ | ✅ |

### Topic-Level Security

**Restricted Topics (Admin/Manager/Owner only):**
- 📢 Official Directives
- 📦 Central Archive
- 📊 Daily Sync
- 👑 Admin Control Panel
- 🗑️ Trash

**Public Topics (All users):**
- 🎨 Brand Repository (read-only for regular users)
- 📋 Task Allocation
- 🐛 Core Operations
- ✅ QA & Review
- ⏰ Attendance & Leave
- 📅 Boardroom
- 💡 Strategic Lounge

### Security Features

**Authentication & Authorization:**
- ✅ Telegram user ID-based authentication
- ✅ Role-based access control (5 roles)
- ✅ Granular permissions per topic
- ✅ Command-level authorization
- ✅ Reaction-level authorization

**Audit & Compliance:**
- ✅ Comprehensive audit trail (all actions logged)
- ✅ Format violation detection
- ✅ Permission violation alerts
- ✅ Message deletion tracking (trash system)
- ✅ User action history
- ✅ Admin alert system

**Data Protection:**
- ✅ Optional database encryption
- ✅ Secure environment variable handling
- ✅ No sensitive data in logs
- ✅ Automatic database backups
- ✅ Data retention policies

**Security Best Practices:**
- ✅ Input validation on all user inputs
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS prevention (Markdown escaping)
- ✅ Rate limiting on commands
- ✅ Error handling without data leakage
- ✅ Secure token storage

### Configuration Security

**Environment Variables:**
```env
# Never commit these to git!
TELEGRAM_BOT_TOKEN=your_secret_token
DATABASE_ENCRYPTION_KEY=your_32_char_key

# Use strong encryption keys
# Generate with: openssl rand -base64 32
```

**File Permissions:**
```bash
# Secure .env file
chmod 600 .env

# Secure database
chmod 600 data/povaly_erp_bot.db

# Secure logs
chmod 600 data/logs/*.log
```

---

## 📞 Support

### Troubleshooting

**Bot Not Responding:**
```bash
# Check if bot is running
./check_bot.sh
ps aux | grep python

# Check logs for errors
tail -f data/logs/errors.log

# Restart bot
./stop_bot.sh
./start_bot_forever.sh

# Verify bot token
echo $TELEGRAM_BOT_TOKEN

# Test bot connection
python -c "from telegram import Bot; bot = Bot('YOUR_TOKEN'); print(bot.get_me())"
```

**Database Issues:**
```bash
# Sync database with Telegram
/syncdb

# Scan topic for missing tasks
/scantopic

# Check database integrity
sqlite3 data/povaly_erp_bot.db "PRAGMA integrity_check;"

# Rebuild database from Telegram (last resort)
# WARNING: This will delete all data not in Telegram!
./stop_bot.sh
rm data/povaly_erp_bot.db
python src/main.py
/scantopic
```

**Permission Issues:**
```bash
# Check user role
/workload @username

# Verify topic IDs in .env
echo $TOPIC_TASK_ALLOCATION

# Check bot permissions in Telegram group
# Bot needs: Read messages, Send messages, Delete messages, Pin messages
```

**Performance Issues:**
```bash
# Check database size
du -h data/povaly_erp_bot.db

# Vacuum database (optimize)
sqlite3 data/povaly_erp_bot.db "VACUUM;"

# Check log file sizes
du -h data/logs/

# Rotate logs
mv data/logs/telegram_bot.log data/logs/telegram_bot.log.old
mv data/logs/errors.log data/logs/errors.log.old
```

### Common Issues

**Issue:** Bot doesn't respond to commands
**Solution:**
1. Check if bot is running: `./check_bot.sh`
2. Check logs: `tail -f data/logs/errors.log`
3. Verify bot token in `.env`
4. Restart bot: `./stop_bot.sh && ./start_bot_forever.sh`

**Issue:** Tasks not showing in `/mytasks`
**Solution:**
1. Run `/syncdb` to sync database
2. Run `/scantopic` in Task Allocation topic
3. Check if task message format is correct
4. Verify user is assigned to task

**Issue:** Reactions not working
**Solution:**
1. Check if message is in correct topic
2. Verify user has permission for reaction
3. Check if task/issue/QA exists in database
4. Run `/syncdb` to sync reactions

**Issue:** Auto check-in not working
**Solution:**
1. Verify `FEATURE_AUTO_CHECKOUT=true` in `.env`
2. Check if user already checked in today
3. Verify task is in ASSIGNED state
4. Check logs for errors

**Issue:** Leave approval not reassigning tasks
**Solution:**
1. Verify `LEAVE_REQUEST_AUTO_REASSIGN_TASKS=true` in `.env`
2. Check if replacement user is specified
3. Verify replacement user exists
4. Check logs for task reassignment errors

### Logs

**View Logs:**
```bash
# Bot logs
tail -f data/logs/telegram_bot.log

# Error logs
tail -f data/logs/errors.log

# Search logs
grep "ERROR" data/logs/telegram_bot.log
grep "Task created" data/logs/telegram_bot.log

# View logs by date
ls -la data/logs/
cat data/logs/telegram_bot.log.2026-05-03
```

**Log Levels:**
- `DEBUG` - Detailed information for debugging
- `INFO` - General information about bot operations
- `WARNING` - Warning messages (non-critical)
- `ERROR` - Error messages (critical)

### Getting Help

**In-Bot Help:**
- `/help` - General help information
- `/commands` - List all available commands
- `/guide` - View topic guides
- `/taskhelp` - Task management guide
- `/qahelp` - QA workflow guide
- `/issuehelp` - Issue tracking guide
- `/attendancehelp` - Attendance guide
- `/meetinghelp` - Meeting guide
- `/birthdayhelp` - Birthday system guide
- `/adminhelp` - Admin commands guide

**Documentation:**
- [BOT_MANAGEMENT.md](./BOT_MANAGEMENT.md) - Bot management guide
- [docs/](./docs/) - Topic-specific guides
- [README.md](./README.md) - This file

**Contact:**
- **Issues:** Report in Admin Control Panel topic
- **Questions:** Ask in Boardroom topic
- **Bugs:** Create issue in GitHub repository
- **Feature Requests:** Discuss in Strategic Lounge topic

### Reporting Bugs

When reporting bugs, include:
1. Bot version (1.0.0)
2. Error message (from logs)
3. Steps to reproduce
4. Expected behavior
5. Actual behavior
6. Screenshots (if applicable)

**Example Bug Report:**
```
**Version:** 1.0.0
**Error:** Task not transitioning to STARTED
**Steps:**
1. Created task with /newtask
2. Reacted with 👍 on task message
3. Task state didn't change

**Expected:** Task should transition to STARTED
**Actual:** Task remains in ASSIGNED state

**Logs:**
[ERROR] Failed to process reaction: Task not found

**Screenshot:** [attached]
```

---

## 📝 License

**Proprietary License**  
Copyright © 2026 Povaly Inc. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use of this software, via any medium, is strictly prohibited.

---

## 🎉 Getting Started

### Quick Start Checklist

- [ ] Clone repository
- [ ] Install dependencies (`./install.sh`)
- [ ] Configure `.env` file
- [ ] Set up Telegram group with topics
- [ ] Add bot to group as admin
- [ ] Configure topic IDs in `.env`
- [ ] Start bot (`./run.sh`)
- [ ] Test with `/help` command
- [ ] Read topic guides (`/guide`)
- [ ] Create first task (`/newtask`)
- [ ] Pin topic guides in each topic

### Next Steps

1. **Read the Guides** - Start with [BOT_MANAGEMENT.md](./BOT_MANAGEMENT.md)
2. **Configure Topics** - Set up all 12 topics in your Telegram group
3. **Add Users** - Configure user roles in `.env`
4. **Pin Guides** - Pin topic guides in each topic (see `docs/PINNING_INSTRUCTIONS.txt`)
5. **Test Workflows** - Create test tasks, issues, QA submissions
6. **Train Team** - Share guides with team members
7. **Monitor** - Check logs and admin alerts regularly

### Resources

- **Documentation:** [docs/](./docs/)
- **Bot Management:** [BOT_MANAGEMENT.md](./BOT_MANAGEMENT.md)
- **GitHub:** [https://github.com/povalygroup/povaly-erp-bot](https://github.com/povalygroup/povaly-erp-bot)
- **Support:** Admin Control Panel topic

---

## 🚀 Version History

### Version 1.0.0 (2026-05-03) - Production Release

**Major Features:**
- ✅ Complete task management system with 7 states
- ✅ QA workflow with approval/rejection and reversals
- ✅ Issue tracking with priority and escalation
- ✅ Attendance system with auto check-in
- ✅ Leave management with task reassignment
- ✅ Meeting coordination with RSVP and reminders
- ✅ Birthday celebration system with auto wishes and reminders
- ✅ Employee information collection (12 fields)
- ✅ Automated reporting (daily, weekly)
- ✅ Reaction-based workflows with smart detection
- ✅ Role-based access control (5 roles)
- ✅ 12 specialized topics with guides
- ✅ 89+ commands (9 new birthday commands)
- ✅ 23+ background services (3 new birthday services)
- ✅ 23 database tables (2 new birthday tables)
- ✅ Comprehensive documentation (3 new birthday guides)

**Technical Improvements:**
- ✅ Reaction reversal system for all workflows
- ✅ Auto-delete DM notifications (30-120s)
- ✅ Smart reaction detection (no spam on swaps)
- ✅ Flexible thumbs up system
- ✅ COMPLETED state separate from APPROVED
- ✅ Context-aware reaction handling
- ✅ Plain text DMs to avoid Markdown errors
- ✅ Trash system for deleted messages
- ✅ Database sync on message deletion
- ✅ Comprehensive audit trail

**Documentation:**
- ✅ Updated all 12 topic guides
- ✅ Added BOT_MANAGEMENT.md
- ✅ Complete README with all features
- ✅ Installation and deployment guides
- ✅ Troubleshooting section
- ✅ Security documentation

---

**Happy Automating! 🚀**

*Built with ❤️ by Povaly Inc.*
