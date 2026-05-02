#!/bin/bash
echo "========================================"
echo "Telegram Operations Bot - Installation"
echo "========================================"
echo ""

echo "Step 1: Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi
echo "✅ Virtual environment created"
echo ""

echo "Step 2: Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

echo "Step 3: Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"
echo ""

echo "Step 4: Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env file created from example"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your bot token and settings!"
else
    echo "ℹ️  .env file already exists"
fi
echo ""

echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your bot token"
echo "2. Run: ./run.sh"
echo ""
