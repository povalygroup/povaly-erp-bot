#!/bin/bash
# Stop the bot and supervisor

echo "Stopping bot..."

# Kill the supervisor script
pkill -f "start_bot_forever.sh"

# Kill the bot
pkill -f "python3 -m src.main"

# Wait a moment
sleep 2

# Check if stopped
if pgrep -f "python3 -m src.main" > /dev/null; then
    echo "❌ Bot still running, forcing stop..."
    pkill -9 -f "python3 -m src.main"
    pkill -9 -f "start_bot_forever.sh"
else
    echo "✅ Bot stopped successfully"
fi

echo "Done!"
