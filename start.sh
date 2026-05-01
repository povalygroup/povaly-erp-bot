#!/bin/bash
# Startup script for Railway deployment

# Set Python path to include the app directory
export PYTHONPATH=/app:$PYTHONPATH

# Create data directory if it doesn't exist
mkdir -p /app/data/logs
mkdir -p /app/data/backups

# Start the bot
python -m src.main
