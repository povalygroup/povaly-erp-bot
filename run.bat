@echo off
echo Starting Telegram Bot...
echo.

python -m src.main

if errorlevel 1 (
    echo.
    echo ❌ Bot failed to start
    echo.
    echo Make sure:
    echo 1. You ran install.bat
    echo 2. You edited .env with your bot token
    echo.
)

pause
