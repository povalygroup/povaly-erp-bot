# Bot Management Guide

## Initial Setup (Run Once)

```bash
cd /home/u531179370/povaly-bot/povaly-erp-bot/
chmod +x setup_bot_management.sh
./setup_bot_management.sh
```

This will create all management scripts and setup auto-restart.

---

## Daily Commands

### Start Bot
```bash
./start_bot.sh
```
Starts bot with auto-restart supervisor. Bot will restart automatically if it crashes.

### Stop Bot
```bash
./stop_bot.sh
```
Stops bot and supervisor completely.

### Restart Bot
```bash
./restart_bot.sh
```
Stops and starts bot (useful after config changes).

### Check Status
```bash
./check_bot.sh
```
Shows if bot is running and recent logs.

### View Live Logs
```bash
./logs.sh
```
Follow logs in real-time (Ctrl+C to stop).

---

## Deployment

### Deploy Updates from GitHub
```bash
./deploy.sh
```
Pulls latest code, stops bot, and restarts with new code.

---

## Database Management

### Clear Database
```bash
./clear_db.sh
```
Deletes database (creates backup first) and restarts with fresh DB.

---

## How Auto-Restart Works

1. **Supervisor Script**: `start_bot_forever.sh` runs in background
2. **Monitors Bot**: If bot crashes, supervisor restarts it in 10 seconds
3. **Cron Backup**: Every 5 minutes, cron checks if supervisor is running
4. **Auto-Recovery**: If supervisor crashes, cron restarts it

---

## Logs

- **Bot Logs**: `data/logs/telegram_bot.log`
- **Supervisor Logs**: `supervisor.log`
- **Cron Logs**: `cron.log`

---

## Troubleshooting

### Bot won't start
```bash
./stop_bot.sh
sleep 5
./start_bot.sh
```

### Check what's wrong
```bash
tail -100 data/logs/telegram_bot.log
tail -50 supervisor.log
```

### Force kill everything
```bash
pkill -9 -f "python3"
pkill -9 -f "start_bot_forever"
./start_bot.sh
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `./start_bot.sh` | Start bot |
| `./stop_bot.sh` | Stop bot |
| `./restart_bot.sh` | Restart bot |
| `./check_bot.sh` | Check status |
| `./deploy.sh` | Deploy updates |
| `./logs.sh` | View live logs |
| `./clear_db.sh` | Clear database |
