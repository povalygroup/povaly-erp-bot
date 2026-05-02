# 🤖 Povaly ERP Bot - Complete Management Guide

This is your complete guide for managing the Povaly ERP Bot on Hostinger. Everything you need to run your bot smoothly in production.

---

## 📋 Table of Contents

1. [Server Connection](#-server-connection)
2. [Bot Control (Start/Stop/Status)](#-bot-control)
3. [Code Updates & Deployment](#-code-updates--deployment)
4. [Configuration Management](#-configuration-management)
5. [Database Management](#-database-management)
6. [Monitoring & Logs](#-monitoring--logs)
7. [Troubleshooting](#-troubleshooting)
8. [Common Workflows](#-common-workflows)
9. [Quick Reference](#-quick-reference)

---

## 🔌 Server Connection

### Connect to Hostinger Server
```bash
ssh -p 65002 u531179370@145.79.25.42
```

### Navigate to Bot Directory
```bash
cd povaly-bot/povaly-erp-bot/
```

### Disconnect from Server
```bash
# Press Ctrl+D or type:
exit
```

**Note:** Bot keeps running after you disconnect (runs in background with `nohup`)

---

## 🎮 Bot Control

### ▶️ Start Bot (24/7 with Auto-Restart)
```bash
nohup ./start_bot_forever.sh &
```

**What this does:**
- Starts bot in background (keeps running after disconnect)
- Auto-restarts if bot crashes (10 second delay)
- Logs everything to `bot.log`
- Runs forever until you manually stop it

**After starting, verify:**
```bash
./check_bot.sh
```

---

### ⏹️ Stop Bot
```bash
./stop_bot.sh
```

**What this does:**
- Stops the supervisor process
- Kills all bot processes
- Cleans up properly

**When to stop:**
- Before pulling code updates
- Before editing critical files
- When troubleshooting issues
- Before server maintenance

---

### 📊 Check Bot Status
```bash
./check_bot.sh
```

**Shows you:**
- ✅ Supervisor status (RUNNING/NOT RUNNING)
- ✅ Bot process status (RUNNING/NOT RUNNING)
- 🔢 Process IDs (PIDs)
- 📝 Recent logs (last 20 lines)

**Example output:**
```
==========================================
Bot Status Check
==========================================
✅ Supervisor: RUNNING
✅ Bot: RUNNING
u531179+ 3690515  3.7  0.0 424916 51128 pts/3    Sl   01:53   0:00 python3 -m src.main

Recent logs:
2026-05-02 01:53:58 - __main__ - INFO - Bot is now running. Press Ctrl+C to stop.
```

---

## 🚀 Code Updates & Deployment

### 📥 Pull Latest Code from GitHub (Deploy Updates)
```bash
# 1. Stop the bot
./stop_bot.sh

# 2. Pull latest code
git pull origin main

# 3. Start the bot
nohup ./start_bot_forever.sh &

# 4. Verify it's running
./check_bot.sh
```

**When to do this:**
- After pushing new features from local machine
- After bug fixes
- After configuration changes in code

---

### 📤 Push Code to GitHub (From Your Local Machine)

#### Step 1: Stage Your Changes
```bash
# Stage all changed files
git add .

# Or stage specific files
git add src/bot/handlers/command_handler.py
```

#### Step 2: Commit Your Changes
```bash
git commit -m "Brief description of what you changed"
```

**Good commit messages:**
- ✅ `"Fix: Resolve QA approval bug"`
- ✅ `"Feature: Add new /report command"`
- ✅ `"Update: Change auto-delete time to 60 seconds"`

**Bad commit messages:**
- ❌ `"fix"`
- ❌ `"update"`
- ❌ `"changes"`

#### Step 3: Push to GitHub
```bash
git push origin main
```

#### Step 4: Deploy to Server
```bash
# SSH into server
ssh -p 65002 u531179370@145.79.25.42

# Navigate to bot directory
cd povaly-bot/povaly-erp-bot/

# Pull and restart
./stop_bot.sh
git pull origin main
nohup ./start_bot_forever.sh &
./check_bot.sh
```

---

### 🔄 Complete Deployment Workflow

**On Local Machine:**
```bash
# 1. Make your changes in code
# 2. Test locally (optional)

# 3. Stage, commit, push
git add .
git commit -m "Your change description"
git push origin main
```

**On Hostinger Server:**
```bash
# 1. Connect
ssh -p 65002 u531179370@145.79.25.42

# 2. Navigate
cd povaly-bot/povaly-erp-bot/

# 3. Deploy
./stop_bot.sh
git pull origin main
nohup ./start_bot_forever.sh &

# 4. Verify
./check_bot.sh
tail -20 bot.log
```

---

## ⚙️ Configuration Management

### Edit Environment Variables (.env)
```bash
# Open .env file in editor
nano .env
```

**Editor controls:**
- **Save:** `Ctrl+O`, then press `Enter`
- **Exit:** `Ctrl+X`
- **Search:** `Ctrl+W`, type search term, press `Enter`

**After editing .env, always restart:**
```bash
./stop_bot.sh
nohup ./start_bot_forever.sh &
```

---

### 🔑 Important .env Variables

#### Bot Configuration
```bash
# Your bot token from @BotFather
TELEGRAM_BOT_TOKEN=8419100961:AAGH5qc3Tr49vjZeCZNH_oYQUNRwY4T70eg

# Your Telegram group ID
TELEGRAM_GROUP_ID=-1003901378950

# Timezone
TIMEZONE=GMT+6
```

#### User Roles (Comma-separated User IDs)
```bash
# Full system access
ADMINISTRATORS=7061459077

# Elevated permissions (leave approval, performance review)
MANAGERS=

# Can approve/reject QA submissions
QA_REVIEWERS=8712619864

# Ownership-level privileges
OWNERS=

# Receive daily summary DMs
ADMIN_DM_RECIPIENTS=
```

#### Topic IDs
```bash
TOPIC_OFFICIAL_DIRECTIVES=2
TOPIC_BRAND_REPOSITORY=4
TOPIC_TASK_ALLOCATION=7
TOPIC_CORE_OPERATIONS=9
TOPIC_QA_REVIEW=11
TOPIC_CENTRAL_ARCHIVE=13
TOPIC_DAILY_SYNC=15
TOPIC_ATTENDANCE_LEAVE=88
TOPIC_ADMIN_CONTROL_PANEL=91
TOPIC_BOARDROOM=19
TOPIC_STRATEGIC_LOUNGE=1
TOPIC_TRASH=5
```

#### Database
```bash
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/povaly_erp_bot.db
DATABASE_BACKUP_TIME=23:00
```

---

### 👥 Add New User Roles

#### Add QA Reviewer
```bash
# 1. Edit .env
nano .env

# 2. Find this line:
QA_REVIEWERS=8712619864

# 3. Add new user ID (comma-separated):
QA_REVIEWERS=8712619864,NEW_USER_ID,ANOTHER_USER_ID

# 4. Save (Ctrl+O, Enter) and exit (Ctrl+X)

# 5. Restart bot
./stop_bot.sh
nohup ./start_bot_forever.sh &
```

#### Add Administrator
```bash
# Same process, edit this line:
ADMINISTRATORS=7061459077,NEW_ADMIN_ID
```

#### Add Manager
```bash
MANAGERS=MANAGER_ID_1,MANAGER_ID_2
```

**How to get user ID:**
- User sends any message to the bot
- Check logs: `grep "user_id" bot.log`
- Or use `/myid` command in bot (if implemented)

---

## 💾 Database Management

### 📦 Backup Database

#### Manual Backup
```bash
# Create backup with timestamp
cp data/povaly_erp_bot.db data/backups/backup_$(date +%Y%m%d_%H%M%S).db

# Example: backup_20260502_143022.db
```

#### View Backups
```bash
ls -lh data/backups/
```

#### Automatic Backups
- Bot automatically backs up daily at time specified in `.env`
- Default: `DATABASE_BACKUP_TIME=23:00` (11:00 PM GMT+6)

---

### 🔍 View Database Contents

#### List All Tables
```bash
sqlite3 data/povaly_erp_bot.db ".tables"
```

#### View Tasks
```bash
sqlite3 data/povaly_erp_bot.db "SELECT ticket, state, assignee_id FROM tasks;"
```

#### View QA Submissions
```bash
sqlite3 data/povaly_erp_bot.db "SELECT ticket, status, submitter_id FROM qa_submissions;"
```

#### View Users
```bash
sqlite3 data/povaly_erp_bot.db "SELECT user_id, username, role FROM users;"
```

#### Count Records
```bash
# Count tasks
sqlite3 data/povaly_erp_bot.db "SELECT COUNT(*) FROM tasks;"

# Count QA submissions
sqlite3 data/povaly_erp_bot.db "SELECT COUNT(*) FROM qa_submissions;"

# Count users
sqlite3 data/povaly_erp_bot.db "SELECT COUNT(*) FROM users;"
```

---

### 🔄 Restore from Backup

```bash
# 1. Stop bot
./stop_bot.sh

# 2. Backup current database (safety)
cp data/povaly_erp_bot.db data/povaly_erp_bot.db.before_restore

# 3. Restore from backup
cp data/backups/BACKUP_FILE_NAME.db data/povaly_erp_bot.db

# 4. Start bot
nohup ./start_bot_forever.sh &

# 5. Verify
sleep 5

./check_bot.sh
```

---

## 📊 Monitoring & Logs

### 📝 View Logs

#### Watch Live Logs (Real-time)
```bash
tail -f bot.log
```
**Stop watching:** Press `Ctrl+C`

#### View Last N Lines
```bash
# Last 50 lines
tail -50 bot.log

# Last 100 lines
tail -100 bot.log

# Last 20 lines (default)
tail bot.log
```

#### View All Logs
```bash
cat bot.log
```

#### Search Logs
```bash
# Search for errors
grep ERROR bot.log

# Search for specific user
grep "user_id=7061459077" bot.log

# Search for specific ticket
grep "GSM260502" bot.log

# Last 20 errors
grep ERROR bot.log | tail -20
```

---

### 📂 Log Files Location

```
data/logs/
├── telegram_bot.log          # Main bot logs
├── telegram_bot.log.2026-04-29  # Rotated logs
├── telegram_bot.log.2026-04-30
├── errors.log                # Error logs only
├── errors.log.2026-04-29
└── errors.log.2026-04-30
```

**View error logs:**
```bash
tail -50 data/logs/errors.log
```

---

### 🔔 Monitor Bot Health

```bash
# Quick health check
./check_bot.sh

# Check recent errors
grep ERROR bot.log | tail -20

# Check if bot is responding
ps aux | grep "python3 -m src.main"

# Check memory usage
ps aux | grep python | awk '{print $4, $11}'

# Check disk space
df -h
```

---

## 🔧 Troubleshooting

### ❌ Bot Not Starting

#### Check for Errors
```bash
tail -50 bot.log
```

#### Check for Stuck Processes
```bash
ps aux | grep python
```

#### Kill Stuck Processes
```bash
pkill -f "python3 -m src.main"
```

#### Try Starting Again
```bash
nohup ./start_bot_forever.sh &
./check_bot.sh
```

---

### ⚠️ Multiple Bot Instances Running

**Error message:** `"Conflict: terminated by other getUpdates request"`

**Solution:**
```bash
# 1. Stop all instances
./stop_bot.sh

# 2. Verify all stopped
ps aux | grep python

# 3. If still running, force kill
pkill -9 -f "python3 -m src.main"

# 4. Start fresh
nohup ./start_bot_forever.sh &

# 5. Verify only one instance
./check_bot.sh
```

---

### 💥 Bot Keeps Crashing

#### Check Logs for Error
```bash
tail -100 bot.log | grep ERROR
```

#### Common Issues:

**1. Database locked:**
```bash
# Stop bot
./stop_bot.sh

# Wait 5 seconds
sleep 5

# Start again
nohup ./start_bot_forever.sh &
```

**2. Invalid token:**
```bash
# Check .env file
grep TELEGRAM_BOT_TOKEN .env

# Make sure token is correct
```

**3. Permission denied:**
```bash
# Fix permissions
chmod +x start_bot_forever.sh
chmod +x stop_bot.sh
chmod +x check_bot.sh
```

---

### 💾 Disk Space Full

#### Check Disk Space
```bash
df -h
```

#### Check Bot Directory Size
```bash
du -sh ~/povaly-bot/povaly-erp-bot/
```

#### Clean Old Logs
```bash
# Remove rotated logs older than 7 days
find data/logs/ -name "*.log.*" -mtime +7 -delete

# Or manually remove specific files
rm data/logs/telegram_bot.log.2026-04-29
```

---

### 🔍 Debug Mode

#### Enable Verbose Logging
```bash
# Edit main.py temporarily
nano src/main.py

# Change logging level from INFO to DEBUG
# logging.basicConfig(level=logging.DEBUG)

# Restart bot
./stop_bot.sh
nohup ./start_bot_forever.sh &
```

**Remember to change back to INFO after debugging!**

---

## 🎯 Common Workflows

### 1️⃣ Deploy New Feature

```bash
# === ON LOCAL MACHINE ===
# Make changes, test, commit
git add .
git commit -m "Feature: Add new command"
git push origin main

# === ON HOSTINGER SERVER ===
ssh -p 65002 u531179370@145.79.25.42
cd povaly-bot/povaly-erp-bot/
./stop_bot.sh
git pull origin main
nohup ./start_bot_forever.sh &
./check_bot.sh
tail -20 bot.log
```

---

### 2️⃣ Add New QA Reviewer

```bash
ssh -p 65002 u531179370@145.79.25.42
cd povaly-bot/povaly-erp-bot/
nano .env

# Add user ID to QA_REVIEWERS line:
# QA_REVIEWERS=8712619864,NEW_USER_ID

# Save: Ctrl+O, Enter
# Exit: Ctrl+X

./stop_bot.sh
nohup ./start_bot_forever.sh &
./check_bot.sh
```

---

### 3️⃣ Check Bot Health (Daily)

```bash
ssh -p 65002 u531179370@145.79.25.42
cd povaly-bot/povaly-erp-bot/

# Quick status
./check_bot.sh

# Check for errors
grep ERROR bot.log | tail -20

# Check database
sqlite3 data/povaly_erp_bot.db "SELECT COUNT(*) FROM tasks;"

# Check disk space
df -h
```

---

### 4️⃣ Backup Database Before Major Changes

```bash
ssh -p 65002 u531179370@145.79.25.42
cd povaly-bot/povaly-erp-bot/

# Create backup
cp data/povaly_erp_bot.db data/backups/backup_before_update_$(date +%Y%m%d_%H%M%S).db

# Verify backup
ls -lh data/backups/

# Now safe to make changes
```

---

### 5️⃣ Investigate User Issue

```bash
ssh -p 65002 u531179370@145.79.25.42
cd povaly-bot/povaly-erp-bot/

# Search logs for user
grep "user_id=USER_ID" bot.log | tail -50

# Check user's tasks
sqlite3 data/test_first_task.db "SELECT * FROM tasks WHERE assignee_id=USER_ID;"

# Check user's QA submissions
sqlite3 data/test_first_task.db "SELECT * FROM qa_submissions WHERE submitter_id=USER_ID;"
```

---

### 6️⃣ Emergency: Restore from Backup

```bash
ssh -p 65002 u531179370@145.79.25.42
cd povaly-bot/povaly-erp-bot/

# Stop bot
./stop_bot.sh

# Backup current (corrupted) database
cp data/povaly_erp_bot.db data/povaly_erp_bot.db.corrupted

# List available backups
ls -lh data/backups/

# Restore from backup
cp data/backups/BACKUP_FILE.db data/povaly_erp_bot.db

# Start bot
nohup ./start_bot_forever.sh &

# Verify
./check_bot.sh
tail -50 bot.log
```

---

## 📖 Quick Reference

### Essential Commands

| Task | Command |
|------|---------|
| **Connect to server** | `ssh -p 65002 u531179370@145.79.25.42` |
| **Go to bot directory** | `cd povaly-bot/povaly-erp-bot/` |
| **Start bot (24/7)** | `nohup ./start_bot_forever.sh &` |
| **Stop bot** | `./stop_bot.sh` |
| **Check status** | `./check_bot.sh` |
| **View live logs** | `tail -f bot.log` |
| **View last 50 logs** | `tail -50 bot.log` |
| **Pull updates** | `git pull origin main` |
| **Edit config** | `nano .env` |
| **Restart bot** | `./stop_bot.sh && nohup ./start_bot_forever.sh &` |
| **Backup database** | `cp data/povaly_erp_bot.db data/backups/backup_$(date +%Y%m%d_%H%M%S).db` |
| **Check disk space** | `df -h` |
| **Search errors** | `grep ERROR bot.log \| tail -20` |

---

### File Locations

| Item | Path |
|------|------|
| **Bot code** | `~/povaly-bot/povaly-erp-bot/` |
| **Main log** | `bot.log` |
| **Error logs** | `data/logs/errors.log` |
| **Database** | `data/povaly_erp_bot.db` |
| **Backups** | `data/backups/` |
| **Configuration** | `.env` |
| **Start script** | `start_bot_forever.sh` |
| **Stop script** | `stop_bot.sh` |
| **Status script** | `check_bot.sh` |

---

### Emergency Commands

| Emergency | Command |
|-----------|---------|
| **Force kill all bot processes** | `pkill -9 -f "python3 -m src.main"` |
| **Force kill supervisor** | `pkill -9 -f "start_bot_forever.sh"` |
| **Check running processes** | `ps aux \| grep python` |
| **Restore from backup** | `cp data/backups/BACKUP.db data/povaly_erp_bot.db` |
| **Clear all logs** | `> bot.log` |
| **Fix permissions** | `chmod +x *.sh` |

---

## 📞 Support & Resources

### Server Information
- **Host:** 145.79.25.42
- **Port:** 65002
- **User:** u531179370
- **Bot Directory:** `/home/u531179370/povaly-bot/povaly-erp-bot/`

### GitHub Repository
- **URL:** https://github.com/povalygroup/povaly-erp-bot

### Important Notes
- ✅ Bot runs 24/7 with auto-restart (10 second delay on crash)
- ✅ Always use `./stop_bot.sh` before pulling code updates
- ✅ Always check `./check_bot.sh` after making changes
- ✅ Backup database before major changes
- ✅ Keep `.env` file secure (never commit to GitHub)
- ✅ Monitor logs regularly for errors

---

**Last Updated:** May 2, 2026  
**Bot Version:** 1.0  
**Maintained by:** Povaly Group
