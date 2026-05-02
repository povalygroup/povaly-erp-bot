#!/bin/bash

# Povaly ERP Bot - Simple Deploy and Restart Script
# Usage: ./deploy_and_restart.sh

echo "========================================="
echo "Povaly ERP Bot - Deploy & Restart"
echo "========================================="

# Navigate to bot directory
cd /home/u531179370/povaly-bot/povaly-erp-bot/

# Stop all running bot instances
echo "Stopping all bot instances..."
pkill -9 -f "main.py" 2>/dev/null || true
pkill -9 python3 2>/dev/null || true
pkill -9 python 2>/dev/null || true
sleep 5

# Verify all stopped
echo "Verifying all instances stopped..."
ps aux | grep "main.py" | grep -v grep || echo "All bot instances stopped"

# Pull latest code
echo "Pulling latest code from GitHub..."
git pull origin main

# Start the bot with correct PYTHONPATH
echo "Starting bot..."
export PYTHONPATH=/home/u531179370/povaly-bot/povaly-erp-bot
nohup python3 src/main.py > nohup.out 2>&1 &

# Wait for bot to start
sleep 5

# Check if bot started successfully
echo ""
echo "========================================="
echo "Bot Status:"
echo "========================================="
tail -20 data/logs/telegram_bot.log

echo ""
echo "========================================="
echo "If you see 'Bot is now running' above, deployment was successful!"
echo "If you see errors, check: tail -50 nohup.out"
echo "========================================="
