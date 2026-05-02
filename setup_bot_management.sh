#!/bin/bash
# Master Setup Script - Creates/Updates All Bot Management Scripts
# Run this once to setup everything

echo "=========================================="
echo "Povaly Bot Management Setup"
echo "=========================================="
echo ""

BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"

# Create start_bot.sh
echo "Creating start_bot.sh..."
cat > "$BOT_DIR/start_bot.sh" << 'EOF'
#!/bin/bash
BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"
cd "$BOT_DIR"

echo "Starting Povaly Bot with auto-restart..."

# Check if already running
if pgrep -f "start_bot_forever.sh" > /dev/null; then
    echo "⚠️  Bot supervisor is already running!"
    echo "Use ./stop_bot.sh first if you want to restart"
    exit 1
fi

# Start supervisor in background
nohup ./start_bot_forever.sh > /dev/null 2>&1 &

sleep 3

# Check if started
if pgrep -f "start_bot_forever.sh" > /dev/null; then
    echo "✅ Bot started successfully!"
    echo ""
    ./check_bot.sh
else
    echo "❌ Failed to start bot"
    tail -30 bot.log
fi
EOF

chmod +x "$BOT_DIR/start_bot.sh"

# Update stop_bot.sh
echo "Updating stop_bot.sh..."
cat > "$BOT_DIR/stop_bot.sh" << 'EOF'
#!/bin/bash
echo "Stopping Povaly Bot..."

# Kill supervisor
pkill -f "start_bot_forever.sh"

# Kill bot
pkill -f "python3 -m src.main"

sleep 2

# Force kill if still running
if pgrep -f "python3 -m src.main" > /dev/null; then
    echo "Force stopping..."
    pkill -9 -f "python3 -m src.main"
    pkill -9 -f "start_bot_forever.sh"
fi

echo "✅ Bot stopped"
EOF

chmod +x "$BOT_DIR/stop_bot.sh"

# Update check_bot.sh
echo "Updating check_bot.sh..."
cat > "$BOT_DIR/check_bot.sh" << 'EOF'
#!/bin/bash
BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"

echo "=========================================="
echo "Bot Status"
echo "=========================================="

# Check supervisor
if pgrep -f "start_bot_forever.sh" > /dev/null; then
    echo "✅ Supervisor: RUNNING"
else
    echo "❌ Supervisor: NOT RUNNING"
fi

# Check bot
if pgrep -f "python3 -m src.main" > /dev/null; then
    echo "✅ Bot: RUNNING"
    echo ""
    echo "Process:"
    ps aux | grep "python3 -m src.main" | grep -v grep
else
    echo "❌ Bot: NOT RUNNING"
fi

echo ""
echo "=========================================="
echo "Recent Logs:"
echo "=========================================="
tail -20 "$BOT_DIR/data/logs/telegram_bot.log"
EOF

chmod +x "$BOT_DIR/check_bot.sh"

# Create deploy.sh
echo "Creating deploy.sh..."
cat > "$BOT_DIR/deploy.sh" << 'EOF'
#!/bin/bash
BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"
cd "$BOT_DIR"

echo "=========================================="
echo "Deploying Povaly Bot"
echo "=========================================="

# Pull latest code
echo "Pulling latest code..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed!"
    exit 1
fi

# Stop bot
echo "Stopping bot..."
./stop_bot.sh
sleep 2

# Start bot
echo "Starting bot..."
./start_bot.sh

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
EOF

chmod +x "$BOT_DIR/deploy.sh"

# Create restart_bot.sh
echo "Creating restart_bot.sh..."
cat > "$BOT_DIR/restart_bot.sh" << 'EOF'
#!/bin/bash
BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"
cd "$BOT_DIR"

echo "Restarting Povaly Bot..."
./stop_bot.sh
sleep 2
./start_bot.sh
EOF

chmod +x "$BOT_DIR/restart_bot.sh"

# Create clear_db.sh
echo "Creating clear_db.sh..."
cat > "$BOT_DIR/clear_db.sh" << 'EOF'
#!/bin/bash
BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"
cd "$BOT_DIR"

echo "⚠️  WARNING: This will delete all data!"
echo "Backup will be created first."
echo ""
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo "Stopping bot..."
    ./stop_bot.sh
    sleep 2
    
    echo "Creating backup..."
    cp data/povaly_erp_bot.db "data/povaly_erp_bot.db.backup_$(date +%Y%m%d_%H%M%S)"
    
    echo "Deleting database..."
    rm data/povaly_erp_bot.db
    
    echo "Starting bot..."
    ./start_bot.sh
    
    echo "✅ Database cleared!"
else
    echo "❌ Cancelled"
fi
EOF

chmod +x "$BOT_DIR/clear_db.sh"

# Create logs.sh
echo "Creating logs.sh..."
cat > "$BOT_DIR/logs.sh" << 'EOF'
#!/bin/bash
BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"

echo "Following bot logs (Ctrl+C to stop)..."
tail -f "$BOT_DIR/data/logs/telegram_bot.log"
EOF

chmod +x "$BOT_DIR/logs.sh"

# Update start_bot_forever.sh
echo "Updating start_bot_forever.sh..."
cat > "$BOT_DIR/start_bot_forever.sh" << 'EOF'
#!/bin/bash
BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"
LOG_FILE="$BOT_DIR/data/logs/telegram_bot.log"
SUPERVISOR_LOG="$BOT_DIR/supervisor.log"
RESTART_DELAY=10

echo "========================================" >> "$SUPERVISOR_LOG"
echo "Supervisor Started: $(date)" >> "$SUPERVISOR_LOG"
echo "========================================" >> "$SUPERVISOR_LOG"

cd "$BOT_DIR" || exit 1

while true; do
    echo "[$(date)] Starting bot..." >> "$SUPERVISOR_LOG"
    
    export PYTHONPATH="$BOT_DIR"
    python3 src/main.py
    
    EXIT_CODE=$?
    echo "[$(date)] Bot stopped (exit: $EXIT_CODE)" >> "$SUPERVISOR_LOG"
    
    echo "[$(date)] Restarting in $RESTART_DELAY seconds..." >> "$SUPERVISOR_LOG"
    sleep $RESTART_DELAY
done
EOF

chmod +x "$BOT_DIR/start_bot_forever.sh"

# Setup cron for monitoring (skip if crontab not available)
echo ""
if command -v crontab &> /dev/null; then
    echo "Setting up cron job for monitoring..."
    (crontab -l 2>/dev/null | grep -v "check_bot_alive.sh"; echo "*/5 * * * * $BOT_DIR/check_bot_alive.sh >> $BOT_DIR/cron.log 2>&1") | crontab -
    echo "✅ Cron job installed"
else
    echo "⚠️  Crontab not available (shared hosting)"
    echo "   Auto-restart will work via supervisor only"
fi

# Create check_bot_alive.sh for cron
cat > "$BOT_DIR/check_bot_alive.sh" << 'EOF'
#!/bin/bash
BOT_DIR="/home/u531179370/povaly-bot/povaly-erp-bot"
cd "$BOT_DIR"

if ! pgrep -f "start_bot_forever.sh" > /dev/null; then
    echo "[$(date)] Bot supervisor not running! Starting..." >> "$BOT_DIR/cron.log"
    nohup ./start_bot_forever.sh > /dev/null 2>&1 &
fi
EOF

chmod +x "$BOT_DIR/check_bot_alive.sh"

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Available commands:"
echo "  ./start_bot.sh    - Start bot with auto-restart"
echo "  ./stop_bot.sh     - Stop bot"
echo "  ./restart_bot.sh  - Restart bot"
echo "  ./check_bot.sh    - Check bot status"
echo "  ./deploy.sh       - Deploy updates from git"
echo "  ./clear_db.sh     - Clear database (with backup)"
echo "  ./logs.sh         - Follow live logs"
echo ""
echo "Cron job installed: Checks every 5 minutes"
echo ""
