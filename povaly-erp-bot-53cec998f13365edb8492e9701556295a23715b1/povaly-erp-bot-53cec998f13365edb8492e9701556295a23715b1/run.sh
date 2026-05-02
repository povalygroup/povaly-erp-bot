#!/bin/bash
echo "Starting Telegram Operations Bot..."
echo ""

# Activate virtual environment if it exists
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# Run the bot
python -m src.main
