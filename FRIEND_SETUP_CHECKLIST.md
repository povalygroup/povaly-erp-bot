# 📋 VPS Setup Checklist - For Your Friend

**What:** Hosting a Python Telegram Bot  
**Time Needed:** 30-45 minutes  
**Difficulty:** Easy (if following steps)

---

## 🎯 What I Need From You

### 1. VPS Access Information

Please provide:

```
IP Address: _________________
SSH Port: ___________________ (usually 22 or 65002)
Username: ___________________
Password: ___________________
```

### 2. VPS Specifications (Minimum)

- **RAM:** 2 GB minimum (4 GB recommended)
- **CPU:** 1 core minimum
- **Storage:** 20 GB minimum (50 GB recommended)
- **OS:** Ubuntu 20.04 or newer (Ubuntu 22.04 LTS preferred)
- **Access:** Root or sudo privileges

### 3. Pre-installed Software (Optional - I can install)

If you can install these, it will save time:
- Python 3.11 or newer
- pip (Python package manager)
- git
- screen or tmux

---

## 🚀 Quick Setup Steps (For You to Follow)

### Step 1: Connect to VPS

```bash
ssh username@ip_address -p port
# Example: ssh u531179370@145.79.25.42 -p 65002
```

### Step 2: Install Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and tools
sudo apt install python3.11 python3.11-venv python3-pip git screen htop nano -y

# Verify Python version
python3.11 --version
```

### Step 3: Create Directory

```bash
mkdir -p ~/povaly-bot/data/logs ~/povaly-bot/data/backups
cd ~/povaly-bot
```

### Step 4: Upload Bot Files

**Option A: I'll upload via SFTP/SCP**
- Just give me the credentials above
- I'll handle the upload

**Option B: You upload for me**
- I'll send you a ZIP file
- Extract it to `/home/username/povaly-bot/`

### Step 5: Setup Python Environment

```bash
cd ~/povaly-bot

# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 6: Create Systemd Service (Auto-start)

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

**Paste this (replace username with actual username):**

```ini
[Unit]
Description=Povaly ERP Telegram Bot
After=network.target

[Service]
Type=simple
User=username
WorkingDirectory=/home/username/povaly-bot
Environment="PATH=/home/username/povaly-bot/venv/bin"
ExecStart=/home/username/povaly-bot/venv/bin/python /home/username/povaly-bot/src/main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/username/povaly-bot/data/logs/telegram_bot.log
StandardError=append:/home/username/povaly-bot/data/logs/errors.log

[Install]
WantedBy=multi-user.target
```

**Save:** Ctrl+X, then Y, then Enter

### Step 7: Enable and Start Bot

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable telegram-bot

# Start bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot
```

**Expected Output:**
```
● telegram-bot.service - Povaly ERP Telegram Bot
   Active: active (running)
```

### Step 8: Verify Bot is Running

```bash
# Check logs
tail -f ~/povaly-bot/data/logs/telegram_bot.log

# Should see:
# ✅ BOT IS NOW RUNNING 24/7
```

---

## 🔧 Useful Commands (For Future Reference)

### Start/Stop/Restart Bot

```bash
sudo systemctl start telegram-bot    # Start
sudo systemctl stop telegram-bot     # Stop
sudo systemctl restart telegram-bot  # Restart
sudo systemctl status telegram-bot   # Check status
```

### View Logs

```bash
# Live logs
tail -f ~/povaly-bot/data/logs/telegram_bot.log

# Error logs
tail -f ~/povaly-bot/data/logs/errors.log

# System logs
sudo journalctl -u telegram-bot -f
```

### Check Resources

```bash
htop              # CPU and memory usage
df -h             # Disk space
free -h           # Memory usage
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: "Python 3.11 not found"

**Solution:**
```bash
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y
```

### Issue 2: "Permission denied"

**Solution:**
```bash
# Make sure you own the directory
sudo chown -R username:username ~/povaly-bot
chmod 644 ~/povaly-bot/data/povaly_erp_bot.db
```

### Issue 3: "Bot crashes immediately"

**Solution:**
```bash
# Check error logs
tail -n 50 ~/povaly-bot/data/logs/errors.log

# Try running manually to see error
cd ~/povaly-bot
source venv/bin/activate
python src/main.py
```

### Issue 4: "Module not found"

**Solution:**
```bash
cd ~/povaly-bot
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🔒 Security Setup (Important!)

### 1. Secure .env File

```bash
chmod 600 ~/povaly-bot/.env
```

### 2. Setup Firewall

```bash
sudo apt install ufw -y
sudo ufw allow 22/tcp      # or your SSH port
sudo ufw enable
sudo ufw status
```

### 3. Disable Root Login (Optional but Recommended)

```bash
sudo nano /etc/ssh/sshd_config

# Change this line:
PermitRootLogin no

# Save and restart SSH
sudo systemctl restart sshd
```

---

## ✅ Final Verification Checklist

After setup, verify:

- [ ] Bot service is running: `sudo systemctl status telegram-bot`
- [ ] Logs show "BOT IS NOW RUNNING 24/7"
- [ ] No errors in error log: `tail ~/povaly-bot/data/logs/errors.log`
- [ ] Bot responds in Telegram group
- [ ] Auto-start enabled: `sudo systemctl is-enabled telegram-bot` (should say "enabled")
- [ ] Firewall configured: `sudo ufw status`
- [ ] .env file secured: `ls -l ~/povaly-bot/.env` (should show -rw-------)

---

## 📞 Contact Me If:

- Bot won't start
- You see errors in logs
- Bot crashes repeatedly
- Need help with any step

**Send me:**
1. Screenshot of error
2. Last 50 lines of error log: `tail -n 50 ~/povaly-bot/data/logs/errors.log`
3. Service status: `sudo systemctl status telegram-bot`

---

## 🎉 Success Indicators

When everything works:

✅ `sudo systemctl status telegram-bot` shows "active (running)"  
✅ Logs show "BOT IS NOW RUNNING 24/7"  
✅ Bot responds to commands in Telegram  
✅ No errors in error log  
✅ Bot survives VPS reboot  

**Thank you for helping me host this bot!** 🙏
