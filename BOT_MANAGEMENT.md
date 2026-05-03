# 🤖 Povaly Bot Management Guide

Complete guide for managing the Telegram bot locally and on Hostinger server.

---

## 📋 Table of Contents
1. [Local Development](#local-development)
2. [Initial Server Setup](#initial-server-setup)
3. [Development Workflow](#development-workflow)
4. [Server Management](#server-management)
5. [Daily Operations](#daily-operations)
6. [Database Management](#database-management)
7. [Troubleshooting](#troubleshooting)
8. [How It Works](#how-it-works)

---

## 💻 Local Development

### Prerequisites
- Python 3.8+
- Git
- Virtual environment (recommended)

### Initial Setup

1. **Clone Repository:**
   ```bash
   git clone <repository-url>
   cd povaly-bot
   ```

2. **Create Virtual Environment (Optional but Recommended):**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment:**
   ```bash
   # Copy template
   cp .env.template .env

   # Edit .env with your settings
   # Windows: notepad .env
   # Linux/Mac: nano .env
   ```

5. **Run Bot:**
   ```bash
   python -m src.main
   ```

### Local Bot Control Commands

#### Windows PowerShell

**Start Bot:**
```powershell
python -m src.main
```

**Stop Bot:**
```powershell
# Press Ctrl+C in the terminal
```

**Clear Database:**
```powershell
# Backup database
Copy-Item data\povaly_erp_bot.db data\backups\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db

# Delete database
Remove-Item data\povaly_erp_bot.db

# Start bot (creates fresh database)
python -m src.main
```

**View Logs:**
```powershell
# View recent logs
Get-Content data\logs\telegram_bot.log -Tail 50

# Follow logs in real-time
Get-Content data\logs\telegram_bot.log -Wait -Tail 50
```

**Check Database:**
```powershell
sqlite3 data\povaly_erp_bot.db
# Inside SQLite:
# .tables          - List all tables
# .schema tasks    - Show table structure
# SELECT * FROM tasks LIMIT 10;
# .quit            - Exit
```

#### Linux/Mac Bash

**Start Bot:**
```bash
python3 -m src.main
```

**Stop Bot:**
```bash
# Press Ctrl+C in the terminal
# Or from another terminal:
pkill -f "python3 -m src.main"
```

**Clear Database:**
```bash
# Backup database
cp data/povaly_erp_bot.db data/backups/backup_$(date +%Y%m%d_%H%M%S).db

# Delete database
rm data/povaly_erp_bot.db

# Start bot (creates fresh database)
python3 -m src.main
```

**View Logs:**
```bash
# View recent logs
tail -50 data/logs/telegram_bot.log

# Follow logs in real-time
tail -f data/logs/telegram_bot.log
```

**Check Database:**
```bash
sqlite3 data/povaly_erp_bot.db
# Inside SQLite:
# .tables          - List all tables
# .schema tasks    - Show table structure
# SELECT * FROM tasks LIMIT 10;
# .quit            - Exit
```

### Local Testing Workflow

1. **Make Code Changes**
2. **Stop Bot** (Ctrl+C)
3. **Clear Database** (optional, for fresh testing)
4. **Start Bot**
5. **Test in Telegram**
6. **Check Logs** for errors
7. **Repeat** until working

### Common Local Commands

```bash
# Check Python version
python --version

# Install/Update dependencies
pip install -r requirements.txt

# Run tests (if available)
pytest

# Check code style
flake8 src/

# Format code
black src/

# Git workflow
git status
git add .
git commit -m "Description"
git push origin main
```

---

## 🚀 Initial Server Setup (Run Once)

### Step 1: Connect to Server
```bash
ssh -p 65002 u531179370@145.79.25.42
# Password: Povabot247@rungrpthis
```

### Step 2: Navigate to Bot Directory
```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
```

### Step 3: Run Master Setup Script
```bash
chmod +x setup_bot_management.sh
./setup_bot_management.sh
```

**This creates:**
- ✅ All management scripts (start, stop, restart, etc.)
- ✅ Auto-restart supervisor
- ✅ Cron job for monitoring (checks every 5 minutes)
- ✅ Log rotation setup

### Step 4: Start Bot
```bash
./start_bot.sh
```

**Done!** Bot is now running 24/7 with auto-restart.

---

## 💻 Development Workflow

### Scenario 1: Change Code Locally → Deploy to Server

**On Your Local Machine:**

1. **Make changes** to code files
2. **Test locally** (optional)
3. **Commit changes:**
   ```bash
   git add .
   git commit -m "Your change description"
   git push origin main
   ```

**On Server:**

4. **Deploy updates:**
   ```bash
   ssh -p 65002 u531179370@145.79.25.42
   cd /home/u531179370/povaly-bot/povaly-erp-bot/
   ./deploy.sh
   ```

**What `./deploy.sh` does:**
- Pulls latest code from GitHub
- Stops the bot
- Restarts bot with new code
- Shows status and logs

**That's it!** Bot is now running with your changes.

---

### Scenario 2: Change .env Config Locally → Update Server

**On Your Local Machine:**

1. **Edit `.env` file** with your changes
2. **Don't commit .env** (it's in .gitignore)
3. **Upload to server:**
   ```bash
   scp -P 65002 .env u531179370@145.79.25.42:/home/u531179370/povaly-bot/povaly-erp-bot/.env
   # Password: Povabot247@rungrpthis
   ```

**On Server:**

4. **Restart bot** to apply config:
   ```bash
   ssh -p 65002 u531179370@145.79.25.42
   cd /home/u531179370/povaly-bot/povaly-erp-bot/
   ./restart_bot.sh
   ```

**Config applied!** Bot is running with new settings.

---

### Scenario 3: Quick Fix Directly on Server

**When to use:** Emergency fixes, testing, or small tweaks.

**On Server:**

1. **Connect and navigate:**
   ```bash
   ssh -p 65002 u531179370@145.79.25.42
   cd /home/u531179370/povaly-bot/povaly-erp-bot/
   ```

2. **Edit file:**
   ```bash
   nano src/path/to/file.py
   # Make changes, save (Ctrl+X, Y, Enter)
   ```

3. **Restart bot:**
   ```bash
   ./restart_bot.sh
   ```

4. **Check if working:**
   ```bash
   ./check_bot.sh
   ./logs.sh  # Watch logs (Ctrl+C to stop)
   ```

5. **If fix works, commit to GitHub:**
   ```bash
   git add .
   git commit -m "Fix: description of fix"
   git push origin main
   ```

**Important:** Always push server changes to GitHub to keep code in sync!

---

### Scenario 4: Update .env Config on Server

**On Server:**

1. **Connect and navigate:**
   ```bash
   ssh -p 65002 u531179370@145.79.25.42
   cd /home/u531179370/povaly-bot/povaly-erp-bot/
   ```

2. **Edit .env:**
   ```bash
   nano .env
   # Make changes, save (Ctrl+X, Y, Enter)
   ```

3. **Restart bot:**
   ```bash
   ./restart_bot.sh
   ```

4. **Verify:**
   ```bash
   ./check_bot.sh
   ```

**Config updated!** Bot is using new settings.

---

## 🖥️ Server Management

### Connect to Server
```bash
ssh -p 65002 u531179370@145.79.25.42
# Password: Povabot247@rungrpthis
```

### Navigate to Bot Directory
```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
```

### Available Commands

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `./start_bot.sh` | Start bot with 24/7 auto-restart | After server reboot or manual stop |
| `./stop_bot.sh` | Stop bot completely | Before maintenance or updates |
| `./restart_bot.sh` | Stop and start bot | After config changes |
| `./check_bot.sh` | Show bot status and logs | Check if bot is running |
| `./deploy.sh` | Pull code from GitHub and restart | Deploy new code |
| `./logs.sh` | Follow live logs | Debug issues (Ctrl+C to stop) |
| `./clear_db.sh` | Clear database (with backup) | Fresh start for testing |

---

## 📅 Daily Operations

### Check Bot Status
```bash
./check_bot.sh
```

**Output shows:**
- ✅ Supervisor running (auto-restart enabled)
- ✅ Bot running
- Recent logs

### Deploy New Code
```bash
./deploy.sh
```

**This automatically:**
1. Pulls latest code
2. Stops bot
3. Starts bot with new code
4. Shows status

### View Live Logs
```bash
./logs.sh
```
Press `Ctrl+C` to stop following logs.

### Restart Bot (After Config Change)
```bash
./restart_bot.sh
```

---

## 🗄️ Database Management

### Local Database Management

#### Clear Database (Fresh Start)

**Windows PowerShell:**
```powershell
# Stop bot (Ctrl+C)

# Backup
Copy-Item data\povaly_erp_bot.db data\backups\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db

# Delete
Remove-Item data\povaly_erp_bot.db

# Start bot
python -m src.main
```

**Linux/Mac:**
```bash
# Stop bot (Ctrl+C)

# Backup
cp data/povaly_erp_bot.db data/backups/backup_$(date +%Y%m%d_%H%M%S).db

# Delete
rm data/povaly_erp_bot.db

# Start bot
python3 -m src.main
```

#### Inspect Database

**Open SQLite:**
```bash
sqlite3 data/povaly_erp_bot.db
```

**Useful SQLite Commands:**
```sql
-- List all tables
.tables

-- Show table structure
.schema tasks
.schema qa_submissions
.schema users

-- View data
SELECT * FROM tasks LIMIT 10;
SELECT * FROM users;
SELECT * FROM qa_submissions WHERE status = 'PENDING';

-- Count records
SELECT COUNT(*) FROM tasks;
SELECT state, COUNT(*) FROM tasks GROUP BY state;

-- Delete specific data
DELETE FROM tasks WHERE state = 'ARCHIVED';
DELETE FROM qa_submissions WHERE status = 'APPROVED';

-- Exit
.quit
```

#### Export/Import Database

**Export (Backup):**
```bash
# Full backup
cp data/povaly_erp_bot.db data/backups/backup_$(date +%Y%m%d).db

# Export to SQL
sqlite3 data/povaly_erp_bot.db .dump > backup.sql
```

**Import (Restore):**
```bash
# Restore from backup
cp data/backups/backup_20260502.db data/povaly_erp_bot.db

# Import from SQL
sqlite3 data/povaly_erp_bot.db < backup.sql
```

### Server Database Management

### Clear Database (Fresh Start)
```bash
./clear_db.sh
```

**What happens:**
1. Asks for confirmation (type `yes`)
2. Stops bot
3. Creates backup: `data/povaly_erp_bot.db.backup_YYYYMMDD_HHMMSS`
4. Deletes database
5. Starts bot (creates fresh database)

### Restore from Backup
```bash
# List backups
ls -lh data/*.backup_*

# Restore specific backup
./stop_bot.sh
cp data/povaly_erp_bot.db.backup_20260502_120000 data/povaly_erp_bot.db
./start_bot.sh
```

---

## 🔧 Troubleshooting

### Bot Not Running

**Check status:**
```bash
./check_bot.sh
```

**Restart:**
```bash
./restart_bot.sh
```

**If still not working:**
```bash
./stop_bot.sh
sleep 5
./start_bot.sh
```

### Bot Keeps Crashing

**View logs:**
```bash
tail -100 data/logs/telegram_bot.log
```

**Check supervisor logs:**
```bash
tail -50 supervisor.log
```

**Common issues:**
- Wrong bot token in `.env`
- Database corruption (use `./clear_db.sh`)
- Python errors (check logs)

### Force Kill Everything

**If bot won't stop:**
```bash
pkill -9 -f "python3"
pkill -9 -f "start_bot_forever"
sleep 2
./start_bot.sh
```

### Deploy Failed

**If `./deploy.sh` fails:**
```bash
# Check git status
git status

# If conflicts, reset to GitHub version
git fetch origin
git reset --hard origin/main

# Try deploy again
./deploy.sh
```

### Cron Not Working

**Check cron job:**
```bash
crontab -l
```

**Should see:**
```
*/5 * * * * /home/u531179370/povaly-bot/povaly-erp-bot/check_bot_alive.sh >> /home/u531179370/povaly-bot/povaly-erp-bot/cron.log 2>&1
```

**Re-setup cron:**
```bash
./setup_bot_management.sh
```

---

## ⚙️ How It Works

### 24/7 Auto-Restart System

**Three layers of protection:**

1. **Supervisor Script** (`start_bot_forever.sh`)
   - Runs in background
   - Monitors bot process
   - If bot crashes → restarts in 10 seconds
   - Logs all restarts to `supervisor.log`

2. **Cron Job** (runs every 5 minutes)
   - Checks if supervisor is running
   - If supervisor crashed → restarts it
   - Logs to `cron.log`

3. **Manual Control** (you)
   - Use `./stop_bot.sh` to stop everything
   - Use `./start_bot.sh` to start everything
   - Use `./check_bot.sh` to verify status

### File Structure

```
povaly-erp-bot/
├── src/                          # Bot source code
├── data/
│   ├── logs/
│   │   └── telegram_bot.log      # Main bot logs
│   └── povaly_erp_bot.db         # Database
├── .env                          # Configuration (not in git)
├── start_bot.sh                  # Start bot
├── stop_bot.sh                   # Stop bot
├── restart_bot.sh                # Restart bot
├── check_bot.sh                  # Check status
├── deploy.sh                     # Deploy from GitHub
├── clear_db.sh                   # Clear database
├── logs.sh                       # View live logs
├── start_bot_forever.sh          # Supervisor (auto-restart)
├── check_bot_alive.sh            # Cron monitor
├── supervisor.log                # Supervisor logs
└── cron.log                      # Cron logs
```

### Log Files

| File | Purpose | View Command |
|------|---------|--------------|
| `data/logs/telegram_bot.log` | Main bot logs | `tail -100 data/logs/telegram_bot.log` |
| `supervisor.log` | Auto-restart logs | `tail -50 supervisor.log` |
| `cron.log` | Cron monitor logs | `tail -50 cron.log` |

---

## 📝 Quick Reference Card

### Local Development Commands

**Windows PowerShell:**
```powershell
# Start bot
python -m src.main

# Stop bot
Ctrl+C

# Clear database
Remove-Item data\povaly_erp_bot.db
python -m src.main

# View logs
Get-Content data\logs\telegram_bot.log -Tail 50

# Follow logs
Get-Content data\logs\telegram_bot.log -Wait -Tail 50
```

**Linux/Mac:**
```bash
# Start bot
python3 -m src.main

# Stop bot
Ctrl+C  # or: pkill -f "python3 -m src.main"

# Clear database
rm data/povaly_erp_bot.db
python3 -m src.main

# View logs
tail -50 data/logs/telegram_bot.log

# Follow logs
tail -f data/logs/telegram_bot.log
```

### Server Commands

### Most Used Commands

```bash
# Connect to server
ssh -p 65002 u531179370@145.79.25.42

# Go to bot directory
cd /home/u531179370/povaly-bot/povaly-erp-bot/

# Deploy new code
./deploy.sh

# Check status
./check_bot.sh

# View logs
./logs.sh

# Restart bot
./restart_bot.sh
```

### Complete Workflow

**Local changes → Server:**
```bash
# Local
git add .
git commit -m "Changes"
git push origin main

# Server
ssh -p 65002 u531179370@145.79.25.42
cd /home/u531179370/povaly-bot/povaly-erp-bot/
./deploy.sh
```

**Config changes:**
```bash
# Upload .env
scp -P 65002 .env u531179370@145.79.25.42:/home/u531179370/povaly-bot/povaly-erp-bot/.env

# Restart
ssh -p 65002 u531179370@145.79.25.42
cd /home/u531179370/povaly-bot/povaly-erp-bot/
./restart_bot.sh
```

---

## ✅ Best Practices

### Local Development
1. **Use virtual environment** to isolate dependencies
2. **Test locally first** before pushing to server
3. **Clear database** when testing new features
4. **Check logs** for errors: `tail -f data/logs/telegram_bot.log`
5. **Commit frequently** with clear messages
6. **Keep .env secure** - never commit to git
7. **Backup database** before major changes

### Server Deployment
1. **Always test locally first** before deploying to server
2. **Commit and push** all changes to GitHub
3. **Use `./deploy.sh`** instead of manual git pull + restart
4. **Check logs** after deployment: `./logs.sh`
5. **Backup database** before clearing: `./clear_db.sh` does this automatically
6. **Never edit code on server** unless emergency (then push to GitHub after)
7. **Keep .env in sync** between local and server
8. **Monitor cron logs** occasionally: `tail -50 cron.log`

### Git Workflow
```bash
# Local changes
git status
git add .
git commit -m "Feature: description"
git push origin main

# Server deployment
ssh -p 65002 u531179370@145.79.25.42
cd /home/u531179370/povaly-bot/povaly-erp-bot/
./deploy.sh
```

---

## 🎯 Development Checklist

### Before Starting Development
- [ ] Virtual environment activated
- [ ] Latest code pulled: `git pull origin main`
- [ ] Dependencies updated: `pip install -r requirements.txt`
- [ ] .env configured correctly
- [ ] Database backed up (if needed)

### Before Committing
- [ ] Code tested locally
- [ ] No errors in logs
- [ ] All features working in Telegram
- [ ] Code formatted (if using formatter)
- [ ] Meaningful commit message ready

### Before Deploying to Server
- [ ] All changes committed and pushed
- [ ] Local testing complete
- [ ] Breaking changes documented
- [ ] .env changes noted (if any)
- [ ] Ready to monitor logs after deployment

---

## 🔍 Debugging Tips

### Local Debugging

**Enable Debug Logging:**
```python
# In src/main.py or config
logging.basicConfig(level=logging.DEBUG)
```

**Check Specific Logs:**
```bash
# Error logs only
grep "ERROR" data/logs/telegram_bot.log

# Specific feature
grep "QA" data/logs/telegram_bot.log

# Recent errors
tail -100 data/logs/telegram_bot.log | grep "ERROR"
```

**Test Database Queries:**
```bash
sqlite3 data/povaly_erp_bot.db
SELECT * FROM tasks WHERE state = 'QA_SUBMITTED';
SELECT * FROM qa_submissions WHERE status = 'PENDING';
.quit
```

**Python Interactive Testing:**
```python
# Start Python REPL
python

# Import and test
from src.config import Config
config = Config()
print(config.TELEGRAM_BOT_TOKEN)
```

### Common Issues

**Bot won't start:**
- Check .env file exists and has correct values
- Check Python version: `python --version`
- Check dependencies: `pip install -r requirements.txt`
- Check logs: `tail -50 data/logs/telegram_bot.log`

**Database errors:**
- Delete and recreate: `rm data/povaly_erp_bot.db`
- Check permissions: `ls -la data/`
- Check disk space: `df -h`

**Import errors:**
- Reinstall dependencies: `pip install -r requirements.txt`
- Check virtual environment is activated
- Check Python path: `echo $PYTHONPATH`

---

## ✅ Best Practices

1. **Always test locally first** before deploying to server
2. **Commit and push** all changes to GitHub
3. **Use `./deploy.sh`** instead of manual git pull + restart
4. **Check logs** after deployment: `./logs.sh`
5. **Backup database** before clearing: `./clear_db.sh` does this automatically
6. **Never edit code on server** unless emergency (then push to GitHub after)
7. **Keep .env in sync** between local and server
8. **Monitor cron logs** occasionally: `tail -50 cron.log`

---

## 🆘 Emergency Contacts

**If bot is completely broken:**

1. Stop everything: `./stop_bot.sh`
2. Check logs: `tail -200 data/logs/telegram_bot.log`
3. Reset to last working version: `git reset --hard <commit-hash>`
4. Start: `./start_bot.sh`

**If server is down:**
- Contact Hostinger support
- Check server status in Hostinger panel

---

**Last Updated:** 2026-05-03  
**Bot Version:** 2.0  
**Features:** COMPLETED state, Auto-delete DMs, Smart reaction detection  
**Server:** Hostinger (145.79.25.42:65002)  
**Local Development:** Windows PowerShell / Linux Bash
