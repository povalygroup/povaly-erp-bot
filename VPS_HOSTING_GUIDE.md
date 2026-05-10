# 🚀 Complete VPS Hosting Guide for Povaly ERP Bot

**Version:** 1.0.0  
**Last Updated:** May 5, 2026  
**Target:** Hostinger VPS (or any Linux VPS)

---

## 📋 Table of Contents

1. [What You Need](#what-you-need)
2. [What to Ask Your Friend](#what-to-ask-your-friend)
3. [VPS Requirements](#vps-requirements)
4. [Files to Upload](#files-to-upload)
5. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
6. [Running the Bot](#running-the-bot)
7. [Auto-Start on Reboot](#auto-start-on-reboot)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

---

## 🎯 What You Need

### From Your Side (Prepare These):

1. **Bot Token** - Already in your `.env` file
2. **Group ID** - Already in your `.env` file
3. **All Bot Files** - Your entire project folder
4. **Database File** - `data/povaly_erp_bot.db` (contains all your data)
5. **Environment File** - `.env` (with all configurations)

### From Your Friend (VPS Provider):

1. **VPS Access Credentials**:
   - IP Address (e.g., `145.79.25.42`)
   - SSH Port (e.g., `65002`)
   - Username (e.g., `u531179370`)
   - Password or SSH Key

2. **VPS Specifications** (Minimum):
   - 1 CPU Core
   - 2 GB RAM (4 GB recommended)
   - 20 GB Storage (50 GB recommended)
   - Ubuntu 20.04+ or Debian 11+

---

## 📦 What to Ask Your Friend

### Tell Your Friend to Provide:

```
Hi! I need to host a Python Telegram bot on a VPS. Can you help me with:

1. VPS Access:
   - IP address
   - SSH port
   - Username
   - Password (or SSH key)

2. VPS Specifications:
   - At least 2 GB RAM
   - Ubuntu 20.04 or newer
   - Root or sudo access

3. Pre-installed (if possible):
   - Python 3.11 or newer
   - pip (Python package manager)
   - git
   - screen or tmux

If these are not installed, I can install them myself with sudo access.
```

---

## 💻 VPS Requirements

### Recommended VPS Plans:

**Hostinger VPS:**
- **KVM 1**: $4-6/month (2 GB RAM, 1 CPU, 50 GB SSD) ✅ Recommended
- **KVM 2**: $8-12/month (4 GB RAM, 2 CPU, 100 GB SSD) ⭐ Best

**Alternative Providers:**
- DigitalOcean Droplet: $6/month (1 GB RAM)
- Vultr Cloud Compute: $6/month (1 GB RAM)
- Linode Nanode: $5/month (1 GB RAM)
- AWS Lightsail: $5/month (1 GB RAM)

### Operating System:
- Ubuntu 22.04 LTS ✅ Recommended
- Ubuntu 20.04 LTS ✅ Good
- Debian 11+ ✅ Good
- CentOS 8+ ⚠️ Works but needs different commands

---

## 📁 Files to Upload

### Required Files (Must Upload):

```
povaly-erp-bot/
├── src/                          # All Python source code
│   ├── bot/
│   ├── core/
│   ├── data/
│   ├── services/
│   ├── security/
│   ├── utils/
│   ├── config.py
│   └── main.py
├── data/                         # Database and logs
│   ├── povaly_erp_bot.db        # ⚠️ IMPORTANT: Your database
│   ├── backups/                  # Optional: backup files
│   └── logs/                     # Will be created automatically
├── .env                          # ⚠️ IMPORTANT: Configuration
├── requirements.txt              # Python dependencies
├── run.sh                        # Run script
└── README.md                     # Documentation (optional)
```

### Files You Can Skip:

```
❌ .git/                          # Git history (not needed)
❌ venv/                          # Virtual environment (create new on VPS)
❌ __pycache__/                   # Python cache (auto-generated)
❌ *.pyc                          # Compiled Python files
❌ .env.template                  # Template (you have .env)
❌ .env.example                   # Example (you have .env)
❌ Dockerfile                     # Docker (not using)
❌ docker-compose.yml             # Docker (not using)
❌ pytest.ini                     # Testing (not needed in production)
❌ setup.py                       # Development (not needed)
❌ Makefile                       # Development (not needed)
```

---

## 🔧 Step-by-Step Setup Guide

### Step 1: Connect to VPS

**On Windows (PowerShell):**
```powershell
ssh u531179370@145.79.25.42 -p 65002
```

**If SSH is blocked by ISP:**
1. Install VPN (Cloudflare WARP): https://1.1.1.1/
2. Or use Hostinger Web Terminal (browser-based)

**On Linux/Mac:**
```bash
ssh u531179370@145.79.25.42 -p 65002
```

Enter password when prompted.

---

### Step 2: Install Required Software

**Update System:**
```bash
sudo apt update && sudo apt upgrade -y
```

**Install Python 3.11+ and Tools:**
```bash
# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install other tools
sudo apt install git screen htop nano curl wget -y

# Verify Python version
python3.11 --version
# Should show: Python 3.11.x or higher
```

**If Python 3.11 is not available:**
```bash
# Add deadsnakes PPA (Ubuntu)
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y
```

---

### Step 3: Create Directory Structure

```bash
# Create main directory
mkdir -p ~/povaly-bot
cd ~/povaly-bot

# Create subdirectories
mkdir -p data/logs data/backups
```

---

### Step 4: Upload Bot Files

**Option A: Using Git (Recommended if you have a repository):**
```bash
cd ~/povaly-bot
git clone https://github.com/your-username/povaly-erp-bot.git .
```

**Option B: Using SFTP (FileZilla, WinSCP, or command line):**

**On Windows (WinSCP):**
1. Download WinSCP: https://winscp.net/
2. Connect:
   - Host: `145.79.25.42`
   - Port: `65002`
   - Username: `u531179370`
   - Password: `your_password`
3. Upload entire `povaly-erp-bot` folder to `/home/u531179370/povaly-bot/`

**On Linux/Mac (scp command):**
```bash
# From your local machine (not VPS)
cd "D:\Work Area\Development\Projects\pova-bot"

# Upload entire directory
scp -P 65002 -r ./* u531179370@145.79.25.42:~/povaly-bot/
```

**Option C: Using rsync (Best for updates):**
```bash
# From your local machine
rsync -avz -e "ssh -p 65002" \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  ./* u531179370@145.79.25.42:~/povaly-bot/
```

---

### Step 5: Setup Python Virtual Environment

```bash
cd ~/povaly-bot

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed python-telegram-bot-21.0 python-dotenv-1.0.0 ...
```

---

### Step 6: Verify Configuration

**Check .env file:**
```bash
cat .env
```

**Verify these are set:**
```env
TELEGRAM_BOT_TOKEN=8419100961:AAFBMBYV1m1UAutifTNQF5Are7egjLIPNOs
TELEGRAM_GROUP_ID=-1003901378950
DATABASE_PATH=./data/povaly_erp_bot.db
```

**If .env is missing, create it:**
```bash
nano .env
# Paste your configuration
# Press Ctrl+X, then Y, then Enter to save
```

---

### Step 7: Verify Database

**Check if database exists:**
```bash
ls -lh data/povaly_erp_bot.db
```

**If database is missing:**
```bash
# The bot will create a new database on first run
# But you'll lose all your data!
# Make sure to upload your existing database file
```

---

### Step 8: Test Run (First Time)

```bash
cd ~/povaly-bot
source venv/bin/activate
python src/main.py
```

**Expected Output:**
```
============================================================
🚀 TELEGRAM BOT STARTING...
============================================================
Loading configuration...
Configuration loaded successfully
Database type: sqlite
Timezone: GMT+6
Initializing database...
Database initialized successfully
Running database migrations...
Database migrations completed
✅ Bot initialization complete
✅ Bot started successfully
✅ All services started
🤖 Bot is now polling for messages...
============================================================
✅ BOT IS NOW RUNNING 24/7
============================================================
```

**If you see errors:**
- Check the error message
- See [Troubleshooting](#troubleshooting) section below

**Stop the test run:**
- Press `Ctrl+C`

---

## 🚀 Running the Bot

### Option 1: Using Screen (Recommended for Beginners)

**Start bot in screen session:**
```bash
# Create screen session
screen -S telegram-bot

# Navigate to bot directory
cd ~/povaly-bot
source venv/bin/activate

# Run bot
python src/main.py
```

**Detach from screen (bot keeps running):**
- Press `Ctrl+A`, then press `D`

**Reattach to screen (to see logs):**
```bash
screen -r telegram-bot
```

**List all screen sessions:**
```bash
screen -ls
```

**Kill screen session:**
```bash
screen -X -S telegram-bot quit
```

---

### Option 2: Using nohup (Simple Background Process)

```bash
cd ~/povaly-bot
source venv/bin/activate

# Run in background
nohup python src/main.py > bot.log 2>&1 &

# Get process ID
echo $!
# Save this number!

# View logs
tail -f bot.log

# Stop bot (replace 12345 with your process ID)
kill 12345
```

---

### Option 3: Using Systemd Service (Best for Production)

**Create service file:**
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

**Paste this configuration:**
```ini
[Unit]
Description=Povaly ERP Telegram Bot
After=network.target

[Service]
Type=simple
User=u531179370
WorkingDirectory=/home/u531179370/povaly-bot
Environment="PATH=/home/u531179370/povaly-bot/venv/bin"
ExecStart=/home/u531179370/povaly-bot/venv/bin/python /home/u531179370/povaly-bot/src/main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/u531179370/povaly-bot/data/logs/telegram_bot.log
StandardError=append:/home/u531179370/povaly-bot/data/logs/errors.log

[Install]
WantedBy=multi-user.target
```

**Save and exit:**
- Press `Ctrl+X`, then `Y`, then `Enter`

**Enable and start service:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable telegram-bot

# Start service
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot
```

**Expected Output:**
```
● telegram-bot.service - Povaly ERP Telegram Bot
   Loaded: loaded (/etc/systemd/system/telegram-bot.service; enabled)
   Active: active (running) since Mon 2026-05-05 10:00:00 UTC; 5s ago
```

**Service Management Commands:**
```bash
# Start bot
sudo systemctl start telegram-bot

# Stop bot
sudo systemctl stop telegram-bot

# Restart bot
sudo systemctl restart telegram-bot

# View status
sudo systemctl status telegram-bot

# View logs (live)
sudo journalctl -u telegram-bot -f

# View last 100 lines
sudo journalctl -u telegram-bot -n 100

# Disable auto-start
sudo systemctl disable telegram-bot
```

---

## 🔄 Auto-Start on Reboot

### If Using Screen:

**Create startup script:**
```bash
nano ~/start-bot.sh
```

**Paste this:**
```bash
#!/bin/bash
cd ~/povaly-bot
source venv/bin/activate
screen -dmS telegram-bot python src/main.py
```

**Make executable:**
```bash
chmod +x ~/start-bot.sh
```

**Add to crontab:**
```bash
crontab -e
```

**Add this line:**
```
@reboot /home/u531179370/start-bot.sh
```

---

### If Using Systemd:

**Already configured!** The service will auto-start on reboot because we used:
```bash
sudo systemctl enable telegram-bot
```

---

## 📊 Monitoring & Maintenance

### Check Bot Status

**If using systemd:**
```bash
sudo systemctl status telegram-bot
```

**If using screen:**
```bash
screen -ls
# Should show: telegram-bot (Detached)
```

**If using nohup:**
```bash
ps aux | grep "python src/main.py"
```

---

### View Logs

**Bot logs:**
```bash
# Live logs
tail -f ~/povaly-bot/data/logs/telegram_bot.log

# Last 100 lines
tail -n 100 ~/povaly-bot/data/logs/telegram_bot.log

# Search for errors
grep "ERROR" ~/povaly-bot/data/logs/telegram_bot.log
```

**Error logs:**
```bash
tail -f ~/povaly-bot/data/logs/errors.log
```

**System logs (if using systemd):**
```bash
sudo journalctl -u telegram-bot -f
```

---

### Check Resource Usage

**CPU and Memory:**
```bash
htop
# Press F10 to exit
```

**Disk Space:**
```bash
df -h
```

**Bot Process:**
```bash
ps aux | grep python
```

---

### Database Backup

**Manual backup:**
```bash
cd ~/povaly-bot/data
cp povaly_erp_bot.db backups/backup_$(date +%Y%m%d_%H%M%S).db
```

**Automatic daily backup (crontab):**
```bash
crontab -e
```

**Add this line (backup at 3 AM daily):**
```
0 3 * * * cp ~/povaly-bot/data/povaly_erp_bot.db ~/povaly-bot/data/backups/backup_$(date +\%Y\%m\%d_\%H\%M\%S).db
```

---

### Update Bot Code

**If using Git:**
```bash
cd ~/povaly-bot

# Stop bot
sudo systemctl stop telegram-bot  # or screen -X -S telegram-bot quit

# Pull latest code
git pull origin main

# Activate venv and update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Start bot
sudo systemctl start telegram-bot  # or screen -dmS telegram-bot python src/main.py
```

**If using manual upload:**
```bash
# Upload new files via SFTP/SCP
# Then restart bot
sudo systemctl restart telegram-bot
```

---

## 🔧 Troubleshooting

### Bot Won't Start

**Check Python version:**
```bash
python3.11 --version
# Must be 3.11 or higher
```

**Check dependencies:**
```bash
cd ~/povaly-bot
source venv/bin/activate
pip list | grep telegram
# Should show: python-telegram-bot 21.0
```

**Check .env file:**
```bash
cat .env | grep TELEGRAM_BOT_TOKEN
# Should show your token
```

**Check database permissions:**
```bash
ls -l data/povaly_erp_bot.db
# Should be readable/writable by your user
```

---

### Bot Crashes Immediately

**View error logs:**
```bash
tail -n 50 ~/povaly-bot/data/logs/errors.log
```

**Common errors:**

1. **"No module named 'telegram'"**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **"Permission denied" on database**
   ```bash
   chmod 644 data/povaly_erp_bot.db
   ```

3. **"Invalid token"**
   - Check TELEGRAM_BOT_TOKEN in .env
   - Make sure there are no spaces or quotes

4. **"Network error"**
   - Check VPS internet connection
   - Try: `ping google.com`

---

### Bot Stops After Disconnect

**If using SSH directly:**
- Use `screen` or `systemd` instead
- SSH sessions close when you disconnect

**If using screen:**
```bash
# Make sure you detached (Ctrl+A, D)
# Not just closed terminal
screen -ls  # Should show (Detached)
```

---

### High Memory Usage

**Check memory:**
```bash
free -h
```

**If bot uses too much memory:**
```bash
# Restart bot
sudo systemctl restart telegram-bot

# Check for memory leaks in logs
grep "memory" ~/povaly-bot/data/logs/telegram_bot.log
```

---

### Database Locked Error

**If you see "database is locked":**
```bash
# Stop bot
sudo systemctl stop telegram-bot

# Check for other processes
ps aux | grep python

# Kill any hanging processes
kill -9 <process_id>

# Start bot
sudo systemctl start telegram-bot
```

---

## 🔒 Security Best Practices

### 1. Secure .env File

```bash
# Set proper permissions (only you can read)
chmod 600 ~/povaly-bot/.env
```

### 2. Firewall Configuration

```bash
# Install UFW (if not installed)
sudo apt install ufw -y

# Allow SSH
sudo ufw allow 65002/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 3. Regular Updates

```bash
# Update system weekly
sudo apt update && sudo apt upgrade -y
```

### 4. Backup Database

```bash
# Backup before any major changes
cp data/povaly_erp_bot.db data/backups/backup_before_update.db
```

### 5. Monitor Logs

```bash
# Check for suspicious activity
grep "ERROR\|WARNING" ~/povaly-bot/data/logs/telegram_bot.log
```

### 6. Limit SSH Access

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Add these lines:
PermitRootLogin no
PasswordAuthentication yes
MaxAuthTries 3

# Restart SSH
sudo systemctl restart sshd
```

---

## 📝 Quick Reference Commands

### Start Bot
```bash
sudo systemctl start telegram-bot
```

### Stop Bot
```bash
sudo systemctl stop telegram-bot
```

### Restart Bot
```bash
sudo systemctl restart telegram-bot
```

### View Status
```bash
sudo systemctl status telegram-bot
```

### View Logs (Live)
```bash
tail -f ~/povaly-bot/data/logs/telegram_bot.log
```

### View Errors
```bash
tail -f ~/povaly-bot/data/logs/errors.log
```

### Backup Database
```bash
cp ~/povaly-bot/data/povaly_erp_bot.db ~/povaly-bot/data/backups/backup_$(date +%Y%m%d).db
```

### Update Bot
```bash
cd ~/povaly-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot
```

---

## ✅ Final Checklist

Before going live, verify:

- [ ] VPS has at least 2 GB RAM
- [ ] Python 3.11+ installed
- [ ] All bot files uploaded
- [ ] .env file configured correctly
- [ ] Database file uploaded
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Bot starts without errors
- [ ] Systemd service configured
- [ ] Auto-start on reboot enabled
- [ ] Logs are being written
- [ ] Database backups scheduled
- [ ] Firewall configured
- [ ] .env file permissions secured

---

## 🆘 Need Help?

If you encounter issues:

1. **Check logs first:**
   ```bash
   tail -n 100 ~/povaly-bot/data/logs/errors.log
   ```

2. **Verify bot is running:**
   ```bash
   sudo systemctl status telegram-bot
   ```

3. **Test bot manually:**
   ```bash
   cd ~/povaly-bot
   source venv/bin/activate
   python src/main.py
   ```

4. **Check system resources:**
   ```bash
   htop
   df -h
   free -h
   ```

---

## 🎉 Success!

Once everything is set up:

✅ Bot runs 24/7 without your PC  
✅ Auto-restarts if it crashes  
✅ Auto-starts after VPS reboot  
✅ Logs all activity  
✅ Backs up database automatically  
✅ No missed notifications  

**Your bot is now production-ready!** 🚀
