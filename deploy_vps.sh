#!/bin/bash
# Deployment script for VPS
# Usage: bash deploy_vps.sh

set -e  # Exit on error

echo "============================================"
echo "🚀 Deploying Telegram Bot to VPS"
echo "============================================"
echo ""

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📂 Working directory: $SCRIPT_DIR"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "💡 Run: python3.11 -m venv venv"
    exit 1
fi

# Backup database before update
echo "💾 Backing up database..."
if [ -f "data/povaly_erp_bot.db" ]; then
    BACKUP_FILE="data/backups/backup_$(date +%Y%m%d_%H%M%S).db"
    cp data/povaly_erp_bot.db "$BACKUP_FILE"
    echo "✅ Database backed up to: $BACKUP_FILE"
else
    echo "⚠️  No database found (first run?)"
fi
echo ""

# Pull latest changes (if using git)
if [ -d ".git" ]; then
    echo "📥 Pulling latest code from git..."
    git pull origin main || echo "⚠️  Git pull failed or not configured"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo ""

# Check if systemd service exists
if systemctl list-unit-files | grep -q "telegram-bot.service"; then
    echo "🔄 Restarting bot service..."
    sudo systemctl restart telegram-bot
    
    # Wait a moment for service to start
    sleep 2
    
    # Check status
    echo ""
    echo "✅ Checking bot status..."
    sudo systemctl status telegram-bot --no-pager -l
    echo ""
    
    echo "============================================"
    echo "🎉 Deployment complete!"
    echo "============================================"
    echo ""
    echo "📊 View live logs:"
    echo "   sudo journalctl -u telegram-bot -f"
    echo ""
    echo "📁 View bot logs:"
    echo "   tail -f data/logs/telegram_bot.log"
    echo ""
    echo "🔍 View error logs:"
    echo "   tail -f data/logs/errors.log"
    echo ""
else
    echo "⚠️  Systemd service not found!"
    echo ""
    echo "💡 To run bot manually:"
    echo "   cd $SCRIPT_DIR"
    echo "   source venv/bin/activate"
    echo "   python src/main.py"
    echo ""
    echo "💡 To create systemd service, see VPS_HOSTING_GUIDE.md"
    echo ""
fi
