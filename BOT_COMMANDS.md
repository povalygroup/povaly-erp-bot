# 🤖 Povaly Bot - Server Management Commands

This file contains all commands you need to manage your bot on Hostinger server.

---

## 📋 **TABLE OF CONTENTS**

1. [Connect to Server](#connect-to-server)
2. [Check Bot Status](#check-bot-status)
3. [View Bot Logs](#view-bot-logs)
4. [Stop Bot](#stop-bot)
5. [Start Bot](#start-bot)
6. [Restart Bot](#restart-bot)
7. [Update Bot Code](#update-bot-code)
8. [Troubleshooting](#troubleshooting)

---

## 🔌 **CONNECT TO SERVER**

**Open PowerShell and run:**

```bash
ssh u531179370@145.79.25.42 -p 65002
```

**Enter password when prompted** (password is invisible while typing - just type and press Enter)

---

## ✅ **CHECK BOT STATUS**

**Check if bot is running:**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
./check_bot.sh
```

**What you'll see:**
- ✅ Supervisor: RUNNING = Auto-restart is active
- ✅ Bot: RUNNING = Bot is working
- Recent logs showing bot activity

---

## 📄 **VIEW BOT LOGS**

**View last 50 lines of logs:**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
tail -n 50 bot.log
```

**View live logs (real-time):**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
tail -f bot.log
```

**Press Ctrl+C to stop viewing** (bot keeps running)

**View supervisor logs (auto-restart history):**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
tail -n 50 supervisor.log
```

---

## 🛑 **STOP BOT**

**Stop bot completely:**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
./stop_bot.sh
```

**What happens:**
- Bot stops immediately
- Auto-restart supervisor stops
- Bot will NOT restart automatically

**Verify bot stopped:**

```bash
./check_bot.sh
```

Should show:
- ❌ Supervisor: NOT RUNNING
- ❌ Bot: NOT RUNNING

---

## ▶️ **START BOT**

**Start bot with auto-restart:**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
nohup ./start_bot_forever.sh &
```

**Wait 5 seconds, then check status:**

```bash
sleep 5
./check_bot.sh
```

Should show:
- ✅ Supervisor: RUNNING
- ✅ Bot: RUNNING

**You can now close PowerShell - bot keeps running!**

---

## 🔄 **RESTART BOT**

**Full restart (stop + start):**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/

# Stop bot
./stop_bot.sh

# Wait 5 seconds
sleep 5

# Start bot
nohup ./start_bot_forever.sh &

# Wait 5 seconds
sleep 5

# Check status
./check_bot.sh
```

---

## 🔄 **UPDATE BOT CODE**

**When you push new code to GitHub:**

```bash
# 1. Connect to server
ssh u531179370@145.79.25.42 -p 65002

# 2. Navigate to bot directory
cd /home/u531179370/povaly-bot/povaly-erp-bot/

# 3. Stop bot
./stop_bot.sh

# 4. Pull latest code from GitHub
git pull origin main

# 5. Check if requirements changed (if yes, install)
pip3 install -r requirements.txt --user

# 6. Start bot
nohup ./start_bot_forever.sh &

# 7. Wait and check status
sleep 5
./check_bot.sh

# 8. View logs to confirm it's working
tail -f bot.log
```

**Press Ctrl+C to stop viewing logs**

---

## 🔧 **TROUBLESHOOTING**

### **Problem: Bot not responding in Telegram**

**Check if bot is running:**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
./check_bot.sh
```

**If bot is NOT running, start it:**

```bash
nohup ./start_bot_forever.sh &
sleep 5
./check_bot.sh
```

**Check logs for errors:**

```bash
tail -n 100 bot.log
```

---

### **Problem: Bot keeps crashing**

**View supervisor log to see crash history:**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
tail -n 100 supervisor.log
```

**View bot error logs:**

```bash
tail -n 100 bot.log | grep -i error
```

**If crashing repeatedly, stop and check logs:**

```bash
./stop_bot.sh
tail -n 200 bot.log
```

---

### **Problem: Database issues**

**Check database file exists:**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
ls -lh data/povaly_bot.db
```

**Check database status:**

```bash
python3 check_bot_status.py
```

---

### **Problem: Bot running but tasks not creating**

**Check if you're posting in correct topic:**
- Tasks must be posted in **Task Allocation** topic (topic ID 7)
- NOT in main chat

**Check logs for task creation:**

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
tail -f bot.log | grep -i task
```

---

### **Problem: Need to see all running processes**

**Check all Python processes:**

```bash
ps aux | grep python3
```

**Kill specific process by ID:**

```bash
kill <process_id>
```

**Force kill if needed:**

```bash
kill -9 <process_id>
```

---

## 📊 **QUICK REFERENCE**

| Task | Command |
|------|---------|
| Connect to server | `ssh u531179370@145.79.25.42 -p 65002` |
| Go to bot directory | `cd /home/u531179370/povaly-bot/povaly-erp-bot/` |
| Check status | `./check_bot.sh` |
| View logs | `tail -f bot.log` |
| Stop bot | `./stop_bot.sh` |
| Start bot | `nohup ./start_bot_forever.sh &` |
| Restart bot | `./stop_bot.sh && sleep 5 && nohup ./start_bot_forever.sh &` |
| Update code | `git pull origin main` |

---

## 🚨 **IMPORTANT NOTES**

1. **Bot runs 24/7 automatically** - No need to keep PowerShell open
2. **Auto-restart enabled** - If bot crashes, it restarts after 10 seconds
3. **After server reboot** - You must manually start bot with `nohup ./start_bot_forever.sh &`
4. **Database location** - `/home/u531179370/povaly-bot/povaly-erp-bot/data/povaly_bot.db`
5. **Logs location** - `/home/u531179370/povaly-bot/povaly-erp-bot/bot.log`
6. **Always check status** - After any change, run `./check_bot.sh`

---

## 📞 **SERVER INFORMATION**

- **Host:** 145.79.25.42
- **Port:** 65002
- **Username:** u531179370
- **Bot Directory:** /home/u531179370/povaly-bot/povaly-erp-bot/
- **Database:** SQLite (./data/povaly_bot.db)
- **Timezone:** GMT+6

---

## ✅ **DAILY CHECKLIST**

**Optional - Check bot health once a day:**

```bash
# 1. Connect
ssh u531179370@145.79.25.42 -p 65002

# 2. Check status
cd /home/u531179370/povaly-bot/povaly-erp-bot/
./check_bot.sh

# 3. View recent logs
tail -n 50 bot.log

# 4. Check supervisor (auto-restart history)
tail -n 20 supervisor.log

# 5. Disconnect
exit
```

---

**Last Updated:** May 2, 2026  
**Bot Version:** Working commit fc3730a  
**Status:** ✅ Running 24/7 on Hostinger
