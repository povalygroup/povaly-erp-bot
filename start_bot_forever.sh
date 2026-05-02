#!/bin/bash
# Bot supervisor script - keeps bot running 24/7 with auto-restart

BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"
LOG_FILE="$BOT_DIR/bot.log"
SUPERVISOR_LOG="$BOT_DIR/supervisor.log"
RESTART_DELAY=10  # Wait 10 seconds before restarting after crash

echo "========================================" >> "$SUPERVISOR_LOG"
echo "Bot Supervisor Started: $(date)" >> "$SUPERVISOR_LOG"
echo "========================================" >> "$SUPERVISOR_LOG"

cd "$BOT_DIR" || exit 1

while true; do
    echo "[$(date)] Starting bot..." >> "$SUPERVISOR_LOG"
    echo "[$(date)] Starting bot..." >> "$LOG_FILE"
    
    # Run the bot
    python3 -m src.main >> "$LOG_FILE" 2>&1
    
    # If we get here, the bot has stopped (crashed or error)
    EXIT_CODE=$?
    echo "[$(date)] Bot stopped with exit code: $EXIT_CODE" >> "$SUPERVISOR_LOG"
    echo "[$(date)] Bot stopped with exit code: $EXIT_CODE" >> "$LOG_FILE"
    
    # Wait before restarting
    echo "[$(date)] Waiting $RESTART_DELAY seconds before restart..." >> "$SUPERVISOR_LOG"
    sleep $RESTART_DELAY
    
    echo "[$(date)] Restarting bot..." >> "$SUPERVISOR_LOG"
done
