#!/bin/bash
# Check if bot is running

echo "=========================================="
echo "Bot Status Check"
echo "=========================================="

# Check if supervisor is running
if pgrep -f "start_bot_forever.sh" > /dev/null; then
    echo "✅ Supervisor: RUNNING"
else
    echo "❌ Supervisor: NOT RUNNING"
fi

# Check if bot is running
if pgrep -f "python3 -m src.main" > /dev/null; then
    echo "✅ Bot: RUNNING"
    
    # Show process details
    echo ""
    echo "Process details:"
    ps aux | grep "python3 -m src.main" | grep -v grep
else
    echo "❌ Bot: NOT RUNNING"
fi

echo ""
echo "=========================================="
echo "Recent logs (last 20 lines):"
echo "=========================================="
tail -n 20 /home/u531179370/povaly-bot/povaly-erp-bot/bot.log

echo ""
echo "=========================================="
echo "Supervisor logs (last 10 lines):"
echo "=========================================="
tail -n 10 /home/u531179370/povaly-bot/povaly-erp-bot/supervisor.log
