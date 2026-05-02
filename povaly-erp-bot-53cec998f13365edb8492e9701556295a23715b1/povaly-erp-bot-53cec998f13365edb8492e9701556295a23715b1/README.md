# Telegram Operations Automation System

Enterprise-grade Telegram bot for managing task workflows, QA reviews, attendance tracking, and automated reporting for Povaly Group.

## Features

- **Task Management**: Reaction-based state transitions with unique ticket identifiers
- **QA Workflow**: Structured submission, review, and approval process
- **Attendance Tracking**: Automated check-in/check-out with late detection
- **Leave Management**: Request submission and approval workflow
- **Automated Reporting**: Daily summaries, sync reports, and weekly analytics
- **Progressive Inactivity Management**: Multi-tier escalation system
- **Violation Detection**: Automated enforcement of format and workflow rules
- **Role-Based Access Control**: Granular permissions across all topics
- **Smart Notifications**: Context-aware routing to appropriate channels

## Quick Start

### Prerequisites

- **Python 3.12 or 3.11** (Python 3.13 NOT supported yet)
- Telegram Bot Token (get from @BotFather)
- Telegram Group ID

⚠️ **IMPORTANT**: Python 3.13 has compatibility issues with python-telegram-bot library. You MUST use Python 3.12 or 3.11.

### Installation (Windows)

1. **Install Python 3.12**
   - Download from: https://www.python.org/downloads/release/python-3120/
   - ☑ Check "Add Python to PATH" during installation
   - If you have Python 3.13, uninstall it first

2. **Run installer**
   ```
   install.bat
   ```
   
   This will:
   - Check Python installation
   - Install all dependencies
   - Create .env file
   - Open .env for editing

3. **Edit .env file**
   - Set `TELEGRAM_BOT_TOKEN` (from @BotFather)
   - Set `TELEGRAM_GROUP_ID` (your group ID)
   - Update topic IDs if needed

4. **Start bot**
   ```
   run.bat
   ```
   Or: `python -m src.main`

### Installation (Linux/Mac)

```bash
# Install dependencies
chmod +x install.sh
./install.sh

# Edit configuration
cp .env.example .env
nano .env  # Set your bot token and group ID

# Run bot
chmod +x run.sh
./run.sh
```

### Configuration

All configuration is managed through the `.env` file. See `.env.template` for a comprehensive list of all available parameters with documentation.

**Required Parameters:**
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot API token
- `TELEGRAM_GROUP_ID`: The Telegram group ID where the bot operates
- `DATABASE_ENCRYPTION_KEY`: 32-character encryption key for sensitive data
- Topic IDs for all 10 topics
- User role assignments (ADMINISTRATORS, MANAGERS, QA_REVIEWERS, OWNERS)

## Architecture

The system follows a layered architecture:

```
Bot Application Layer → Business Logic Layer → Service Layer → Data Access Layer
```

### Key Components

- **Message Handler**: Processes incoming Telegram messages and reactions
- **Topic Router**: Routes messages to appropriate handlers based on topic
- **State Engine**: Manages task state transitions
- **Violation Detection**: Identifies and handles rule violations
- **Notification Router**: Routes notifications to appropriate channels
- **Scheduler**: Triggers time-based operations
- **Report Generator**: Generates formatted reports

### Database Support

The system supports three database backends:
- **SQLite** (default): Lightweight, embedded database
- **MongoDB**: Distributed, scalable database
- **JSON**: File-based storage for development/testing

Switch between databases by changing `DATABASE_TYPE` in `.env`.

## Usage

### Task Workflow

1. **Create Task**: Post message with TICKET identifier in Task Allocation topic
   ```
   [PV-2404-1] @username Create video thumbnail
   ```

2. **Start Task**: Add 👍 reaction to task message

3. **Submit for QA**: Post in QA & Review topic
   ```
   [PV-2404-1][PV][Video thumbnail]
   ```

4. **Approve/Reject**: QA Reviewer adds ❤️ (approve) or 👎 (reject) reaction

5. **Provide Feedback** (if rejected): Post rejection details
   ```
   [PV-2404-1][Quality Issue][Low resolution][Increase to 1080p][@username]
   ```

### Attendance

- **Check-in**: Automatically recorded on first 👍 reaction of the day
- **Check-out**: Post check-out command in Attendance & Leave topic or auto check-out at 23:59

### Leave Requests

Post leave request in Attendance & Leave topic:
```
Leave request: 2024-01-15 to 2024-01-17
Reason: Personal
```

Manager approves with ❤️ or rejects with 👎 reaction.

## Reports

### Daily Summary Messages (00:00 GMT+6)
- Posted to Task Allocation and QA Review topics
- Shows pending tasks grouped by assignee/reviewer
- Includes starting ticket ID for the day

### Daily Sync Reports (22:30 GMT+6)
- Per-user task progress reports
- Posted to Daily Sync topic
- Includes completed, started, not touched, and rejected tasks

### Weekly Reports (Sunday 22:30 GMT+6)
- Team performance analytics
- Top performers and performance alerts
- Posted to Daily Sync topic

## Development

### Project Structure

```
telegram-ops-automation/
├── src/                    # Source code
│   ├── bot/               # Bot application layer
│   ├── core/              # Business logic layer
│   ├── services/          # Service layer
│   ├── data/              # Data access layer
│   ├── security/          # Security and access control
│   └── utils/             # Utility functions
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── docs/                  # Documentation
└── data/                  # Runtime data directory
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration
```

### Database Management

```bash
# Initialize database
python scripts/setup_database.py

# Backup database
python scripts/backup_database.py --output ./backups/backup-$(date +%Y%m%d).db

# Restore from backup
python scripts/restore_database.py --input ./backups/backup-20240115.db

# Migrate between database types
python scripts/migrate_database.py --source sqlite --target mongodb
```

## Deployment

### Docker Compose

See `docker-compose.yml` for multi-container setup with MongoDB.

### systemd Service

See `docs/deployment.md` for systemd service configuration.

### Cloud Platforms

The system can be deployed to:
- AWS ECS
- Google Cloud Run
- Azure Container Instances
- Any Docker-compatible platform

## Monitoring

### Health Checks

The bot includes built-in health checks for:
- Database connectivity
- Telegram API connectivity
- Scheduler status
- System uptime

### Logging

- Structured JSON logs
- Daily log rotation
- Configurable retention period
- Separate logs for different components

### Metrics

- Message processing rate
- Database query performance
- Notification delivery success rate
- Scheduled job execution time
- Error rates by category

## Security

- Role-based access control with 4 user roles
- Granular permissions per topic
- Encrypted storage of sensitive data
- Comprehensive audit trail
- Permission violation detection and logging

## Support

For issues, questions, or contributions, please refer to the project documentation in the `docs/` directory.

## License

[Your License Here]
