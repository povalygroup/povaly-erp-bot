@echo off
echo Connecting to Hostinger server...
echo.

plink -ssh -P 65002 u531179370@145.79.25.42 -pw "Povabot247@rungrpthis" "cd /home/u531179370/povaly-bot/povaly-erp-bot/ && git pull origin main && pkill -9 python3 && export PYTHONPATH=/home/u531179370/povaly-bot/povaly-erp-bot && nohup python3 src/main.py > nohup.out 2>&1 & sleep 3 && tail -30 data/logs/telegram_bot.log"

echo.
echo Deployment complete!
pause
