# 🚀 Povaly ERP Bot - Telegram Operations Automation System

A comprehensive enterprise-grade Telegram bot for managing task workflows, QA reviews, attendance tracking, issue management, and automated reporting.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Commands](#commands)
- [Topic Guides](#topic-guides)
- [Deployment](#deployment)
- [Support](#support)

---

## 🎯 Overview

Povaly ERP Bot is a multi-functional Telegram automation system designed for teams to:
- **Manage Tasks** - Create, assign, track, and complete tasks with state transitions
- **QA Reviews** - Submit work for review and manage approval workflows
- **Track Issues** - Report, claim, and resolve issues with escalation
- **Monitor Attendance** - Auto check-in, track breaks, manage leave requests
- **Generate Reports** - Daily summaries, performance metrics, analytics
- **Enforce Compliance** - Detect violations, track audit trails, role-based access

**Current Status:** 95% Complete | 60+ Commands | 18 Services | 21 Database Tables

---

## ✨ Key Features

### Task Management
- ✅ Task creation with automatic ticket generation
- ✅ Reaction-based state transitions (👍 start, ❤️ approve, 👎 reject, 🔥 urgent)
- ✅ Multiple assignees per task
- ✅ Task dependencies (blocking relationships)
- ✅ Deadline reminders (24-hour and 1-hour warnings)
- ✅ Bulk task assignment
- ✅ Smart task routing based on workload and expertise
- ✅ Task archival with completion time tracking

### QA Workflow
- ✅ QA submission with brand/asset tracking
- ✅ Multiple QA reviewers per submission
- ✅ Approval/rejection workflow
- ✅ Rejection feedback with issue tracking
- ✅ QA escalation for pending submissions
- ✅ QA reminders for old submissions

### Issue Management
- ✅ Issue creation from tasks
- ✅ Priority levels (LOW, MEDIUM, HIGH, CRITICAL)
- ✅ Multiple issue handlers
- ✅ Issue claiming and resolution
- ✅ Issue escalation for unclaimed issues
- ✅ Issue reminders and tracking

### Attendance & Leave
- ✅ Automatic check-in on first task
- ✅ Manual check-in/check-out
- ✅ Late check-in detection
- ✅ Break tracking with limits
- ✅ Leave request management
- ✅ Task reassignment during leave
- ✅ Leave approval workflow

### Automated Reporting
- ✅ Daily task summaries (00:00 GMT+6)
- ✅ Daily sync reports (22:30 GMT+6)
- ✅ Weekly performance reports (Sunday 22:30)
- ✅ Performance metrics and analytics
- ✅ Top performers tracking

### Security & Compliance
- ✅ Role-based access control (5 roles)
- ✅ Granular permissions per topic
- ✅ Format violation detection
- ✅ Comprehensive audit trail
- ✅ Permission violation alerts
- ✅ Encrypted data storage

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot Layer                        │
│  (Command Handler, Message Handler, Reaction Handler)       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Business Logic Layer                        │
│  (Task Service, QA Service, Issue Service, etc.)            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Service Layer                              │
│  (18 Background Services, Schedulers, Escalation)           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 Data Access Layer                            │
│  (12 Repositories, Database Adapters)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Database Layer                              │
│  (SQLite, MongoDB, JSON - Configurable)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- Telegram Bot Token
- Telegram Group with Topics enabled
- Git

### Quick Start

1. **Clone Repository**
```bash
git clone https://github.com/povaly/povaly-erp-bot.git
cd povaly-erp-bot
```

2. **Install Dependencies**
```bash
./install.sh
# or
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
cp .env.template .env
# Edit .env with your settings
```

4. **Start Bot**
```bash
./start_bot_forever.sh
# or
python src/main.py
```

### Docker Deployment

```bash
docker-compose up -d
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
BRAND_CODES=POV,BRD,MKT,DEV,QA

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
```

---

## 🎮 Usage

### Basic Workflow

1. **Create Task**
   ```
   /newtask
   → Select brand
   → Enter task details
   → Task created and assigned
   ```

2. **Start Working**
   - React with 👍 to task message
   - Status changes to STARTED
   - Auto check-in recorded

3. **Submit for QA**
   ```
   /newqa
   → Select task
   → Submit for review
   ```

4. **QA Review**
   - Reviewer reacts with 👍 to approve
   - Or 👎 to reject with feedback

5. **Complete Task**
   - React with ❤️ to confirm completion
   - Task archived automatically

### Common Commands

```
/help              - Show help information
/commands          - Show all available commands
/mytasks           - View your assigned tasks
/myissues          - View issues you created
/myleave           - View your leave requests
/myattendance      - View your attendance
/checkin           - Manual check-in
/checkout          - Manual check-out
```

---

## 📚 Commands

See `/commands` in bot for complete list with role-based filtering.

**Quick Reference:**
- **Task Commands:** `/newtask`, `/mytasks`, `/tasksbystate`, `/bulkassign`, `/block`, `/unblock`
- **QA Commands:** `/newqa`, `/myqa`, `/pendingqa`, `/approve`, `/reject`
- **Issue Commands:** `/newissue`, `/myissues`, `/openissues`, `/close`, `/reopen`
- **Attendance Commands:** `/checkin`, `/checkout`, `/break`, `/myattendance`
- **Leave Commands:** `/requestleave`, `/myleave`, `/pendingleave`
- **Admin Commands:** `/workload`, `/assignto`, `/pendingleave`, `/attendance`

---

## 📖 Topic Guides

Each topic has a dedicated guide document:

1. **Official Directives** - Company announcements and policies
2. **Brand Repository** - Brand assets and guidelines
3. **Task Allocation** - Task creation and assignment
4. **Core Operations** - Issue management and tracking
5. **QA Review** - Quality assurance submissions
6. **Central Archive** - Completed tasks archive
7. **Daily Sync** - Daily reports and summaries
8. **Attendance & Leave** - Attendance tracking and leave requests
9. **Admin Control Panel** - Admin alerts and notifications
10. **Boardroom** - Meeting notes and discussions
11. **Strategic Lounge** - Strategy and planning
12. **Trash** - Deleted messages archive

See [Topic Guides](./docs/TOPIC_GUIDES.md) for detailed information.

---

## 🚀 Deployment

### Production Deployment

1. **Server Setup**
   ```bash
   # SSH into server
   ssh user@145.79.25.42:65002
   
   # Navigate to bot directory
   cd /home/u531179370/povaly-bot/povaly-erp-bot/
   ```

2. **Deploy Code**
   ```bash
   git pull origin main
   ./stop_bot.sh
   ./start_bot_forever.sh
   ./check_bot.sh
   ```

3. **Monitor**
   ```bash
   tail -f data/logs/telegram_bot.log
   ```

### Docker Deployment

```bash
docker-compose -f docker-compose.yml up -d
docker-compose logs -f
```

---

## 📊 Database

### Supported Databases
- **SQLite** (default) - File-based, no setup required
- **MongoDB** - For large-scale deployments
- **JSON** - For simple file-based storage

### Backup

Automatic backups run daily at 23:00 GMT+6.

Manual backup:
```bash
cp data/povaly_erp_bot.db data/backups/povaly_erp_bot.db.backup
```

---

## 🔐 Security

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **REGULAR** | Create tasks, submit QA, report issues, check-in/out |
| **QA_REVIEWER** | Approve/reject QA submissions |
| **MANAGER** | Approve leave, view team workload, escalate issues |
| **ADMIN** | Full system access, manage users, view all data |
| **OWNER** | System configuration, database management |

### Topic Restrictions

Restricted topics (only admins/managers/owners can post):
- Official Directives
- Central Archive
- Daily Sync
- Admin Control Panel
- Trash

---

## 📞 Support

### Troubleshooting

**Bot not responding:**
```bash
./check_bot.sh
./stop_bot.sh
./start_bot_forever.sh
```

**Database issues:**
```bash
/syncdb          # Sync database with Telegram
/resetdb         # Reset database
/scantopic       # Scan topic for tasks
```

**View logs:**
```bash
tail -f data/logs/telegram_bot.log
tail -f data/logs/errors.log
```

### Contact

- **Issues:** Report in Admin Control Panel
- **Questions:** Ask in Boardroom topic
- **Bugs:** Create issue in repository

---

## 📝 License

Proprietary - Povaly Inc.

---

## 🎉 Getting Started

1. Read the [Topic Guides](./docs/TOPIC_GUIDES.md)
2. Run `/help` in bot for quick reference
3. Run `/commands` to see all available commands
4. Start creating tasks with `/newtask`

**Happy automating!** 🚀
