@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Telegram Bot - Installation
echo ========================================
echo.

REM Check if Python works
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not working on your system
    echo.
    echo Your Python 3.13 installation is corrupted.
    echo.
    echo SOLUTION:
    echo 1. Uninstall Python from Windows Settings
    echo 2. Download Python 3.12 from: https://www.python.org/downloads/
    echo 3. Install with "Add Python to PATH" checked
    echo 4. Run this script again
    echo.
    echo Opening Python download page...
    start https://www.python.org/downloads/release/python-3120/
    echo.
    pause
    exit /b 1
)

echo ✅ Python found:
python --version
echo.

echo Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    echo.
    echo Try running as Administrator
    pause
    exit /b 1
)
echo ✅ Dependencies installed
echo.

if not exist .env (
    copy .env.example .env >nul
    echo ✅ Created .env file
    echo.
    echo Opening .env in Notepad...
    echo Update TELEGRAM_BOT_TOKEN and TELEGRAM_GROUP_ID
    echo.
    timeout /t 2 >nul
    notepad .env
) else (
    echo ℹ️  .env already exists
)

echo.
echo ========================================
echo ✅ Installation Complete!
echo ========================================
echo.
echo To start bot: python -m src.main
echo Or run: run.bat
echo.
pause
